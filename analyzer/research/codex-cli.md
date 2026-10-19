# Codex CLI transcript schema

Catalog agent: `codex-cli`. OpenAI Codex CLI (the Rust `codex-rs`
workspace, also behind the VS Code extension and the desktop app) writes one
append-only JSONL "rollout" per thread, each line an envelope around a
tagged item, plus a global prompt history. Open Interpreter is a fork that
keeps the format byte for byte under `~/.openinterpreter`; see
[open-interpreter.md](open-interpreter.md), which records only what differs.
The parser is `doubleagent/parsers/codex.py` (`CodexParser`, built on the
shared `RolloutParser`).

Paths and the rest of the per-user state are in
[`collectors/research/codex-cli.md`](../../collectors/research/codex-cli.md).

## 1. Evidence

- **Source**: [openai/codex](https://github.com/openai/codex) at
  [`3e238776e857eccd3bde6bff3026e2e9798f6524`](https://github.com/openai/codex/commit/3e238776e857eccd3bde6bff3026e2e9798f6524)
  (2026-10-03), Apache-2.0, open source, the commit the [collector document](../../collectors/research/codex-cli.md)
  cites. Paths below are relative to `codex-rs/`. Every schema claim is
  from source unless marked **local**.
- **Local**: the real install on the development host, Codex 0.160.0
  (`session_meta.cli_version`), one rollout of 20 lines, a 1-line
  `history.jsonl` and a 1-line `session_index.jsonl`, plus scratchpad copies
  of `state_5.sqlite` and `thread_history_1.sqlite`. Only record types, key
  paths, value types and enum values were tabulated; no content was read
  into this document. The one rollout is `history_mode: "paginated"` and
  has no `git` block, so the legacy event set and `git` are source only.
- **Observed (Windows)**: the author's Windows 11 ARM64 lab VM (`ver`
  prints `10.0.26300.9550`), 2026-10-15, times in UTC, read for file
  names, sizes, key names, value types, enum values and row counts only
  (issues 113 and 118). The Codex here is Codex Desktop, the copy of Codex
  bundled in the ChatGPT desktop app, installed from the Microsoft Store as
  the MSIX package `OpenAI.Codex` 26.1007.9446.0 (MSIX is the Windows app
  package format); its rollouts name it `originator` `Codex Desktop`,
  `cli_version` `0.162.0-alpha.17.2`. It writes to the standard
  `CODEX_HOME`, `~\.codex`. The paths and the app's other directories are
  in [`collectors/research/chatgpt-desktop.md`](../../collectors/research/chatgpt-desktop.md)
  and [`collectors/research/codex-cli.md`](../../collectors/research/codex-cli.md).
  The user asked a question in a plain chat, generated an image and ran
  a task in a project folder; no listing was taken between tasks, so the
  mapping from task to file is by modification time only.
  - Two rollouts under `sessions/2026/10/15/`, both
    `history_mode` `paginated`, 0 bad lines. The first (37 lines:
    `session_meta` 1, `turn_context` 1, `world_state` 1, `response_item`
    17, `event_msg` 13, `token_usage_record` 4) ran 14:26:37Z to
    14:27:19Z in the app's default output directory for a thread with no
    project, `~\Documents\Codex\2026-10-15\d`; the second (32 lines:
    `session_meta` 1, `turn_context` 1, `world_state` 1, `response_item`
    15, `event_msg` 11, `token_usage_record` 3) ran 14:30:05Z to
    14:32:47Z in a project folder on the Desktop and wrote eleven files
    there. The file-name time is local time, as on the CLI. The parser
    gave 27 and 23 rows: user turns, assistant messages, `exec`, `shell`,
    `web_search` and `apply_patch` calls, `task_started` and
    `task_complete`, `model: gpt-6-luna` and one `permission mode:` row
    each.
  - `session_meta.payload` keys: `id`, `session_id`, `timestamp`, `cwd`,
    `runtime_workspace_roots` (1 entry), `originator` `Codex Desktop`,
    `cli_version`, `source` `vscode`, `thread_source` `user`,
    `model_provider` `openai`, `base_instructions` (`text`, and
    `provenance` with `type` `model` and `model`), `history_mode`
    `paginated`, `context_window` (`window_id`), `creator_user_id` (29
    characters) and `creator_account_id` (36 characters, a UUID). Every
    top-level key is in the source list in
    [section 3](#3-record-envelope-and-types); `base_instructions.provenance`
    is observed, not checked against source at [3e23877](https://github.com/openai/codex/commit/3e238776e857eccd3bde6bff3026e2e9798f6524). No `git` block
    (neither directory was a repository). `source` is `vscode` for these
    desktop threads, so `originator` is the key that names the desktop
    app.
  - `turn_context.payload` keys: `turn_id`, `root_turn_id`, `cwd`,
    `workspace_roots` (2), `current_date`, `timezone`, `approval_policy`
    `on-request`, `sandbox_policy` (`type`
    `workspace-write`, `writable_roots`, `network_access`,
    `exclude_tmpdir_env_var`, `exclude_slash_tmp`), `permission_profile`
    (`type` `managed`, `file_system` with `type` `restricted` and 13
    `entries`, `network` `restricted`), `model` `gpt-6-luna`,
    `collaboration_mode` (`mode` `default`, `settings` with `model`,
    `reasoning_effort` `medium` and `developer_instructions`), `effort`
    `medium`, `summary` `detailed`, `personality` `friendly`. Observed
    and not among the fields [section 3](#3-record-envelope-and-types)
    lists from source at [3e23877](https://github.com/openai/codex/commit/3e238776e857eccd3bde6bff3026e2e9798f6524) (whether that commit's struct already
    has them was not rechecked): `disabled_plugin_ids`,
    `approvals_reviewer` `user`, `active_permission_profile` (`id`
    `:workspace`), `file_system_sandbox_policy` (`kind` `restricted`, 13
    `entries`), `comp_hash`, `multi_agent_version` `v2`,
    `realtime_active`, `cyber_access_program` `standard`. The parser
    reads none of them.
  - `state_5.sqlite` `threads` (2 rows) had the columns `id`,
    `rollout_path`, `created_at`, `updated_at`, `source`,
    `model_provider`, `cwd`, `title`, `sandbox_policy`, `approval_mode`,
    `tokens_used`, `has_user_event`, `archived`, `archived_at`, `git_sha`,
    `git_branch`, `git_origin_url`, `cli_version`, `first_user_message`,
    `agent_nickname`, `agent_role`, `memory_mode`, `model`,
    `reasoning_effort`, `agent_path`, `created_at_ms`, `updated_at_ms`,
    `thread_source`, `preview`, `recency_at`, `recency_at_ms`,
    `history_mode`, `name`, `is_pinned`, `thread_section_id`,
    `section_position`, `section_entered_at_ms`, `project_id`,
    `originator`, `daybreak_enabled`, `creator_user_id`,
    `creator_account_id`. `approval_mode` held the approval policy: the
    first thread's a JSON object `{"granular": {"sandbox_approval":
    false, "rules": false, "skill_approval": false,
    "request_permissions": true, "mcp_elicitations": true}}`, the
    second's the string `on-request`; `sandbox_policy` held JSON of 2,389
    and 1,725 characters. The first thread's rollout row
    (`permission mode:`) carries the same granular object. The database
    also held `projects` (1 row), `project_roots` (1), `thread_sections`
    (1), `remote_control_enrollments` (0) and
    `external_agent_config_imports` (0) beside the tables the source
    describes.
  - `thread_history_1.sqlite` `thread_items` (13 rows): `item_type`
    `agentMessage` 4, `commandExecution` 2, `fileChange` 1, `reasoning`
    2, `userMessage` 2, `webSearch` 2; `thread_turns` 2 rows, both
    `status` `completed`.
  - The ChatGPT chat and the image generation left no rollout and no row
    in `state_5.sqlite` or `thread_history_1.sqlite`; their only local
    trace is in the desktop app's own `sqlite/codex-dev.db`
    ([section 5](#5-other-files)) and `.codex-global-state.json`. A first
    attempt to create a scheduled automation failed in the app and wrote
    nothing.
  - Later the same day (third survey 15:30Z), after the account was
    subscribed to ChatGPT Plus, the user created a scheduled automation
    that saved, and connected a GitHub account. The automation wrote
    `automations/<slug>/automation.toml` and one `codex-dev.db`
    `automations` row ([section 5](#5-other-files)), and at once created
    its target thread: a third rollout
    (`rollout-2026-10-15T11-25-49-<uuid>.jsonl`, 83,579 bytes, 15:25:50Z)
    in a new default output directory `~\Documents\Codex\2026-10-15\new-chat`,
    `thread_source` `user`, `source` `vscode`, `originator`
    `Codex Desktop`, approval `on-request`, on model `gpt-5.6-terra`, not
    the `gpt-6-luna` of the two earlier threads (the app chose it for the
    automation). It held one user turn (the automation's prompt), one
    assistant message and no tool call, `task_started` to
    `task_complete` in 9,969 ms; the parser gave 12 rows (10 `system`, 1
    `user`, 1 `assistant`) with the usual `session start:`, `model:` and
    `permission mode:` rows. The automation had not fired by the survey:
    `automation_runs` and `inbox_items` were still empty. The account
    took a token refresh in `auth.json` and a longer `models_cache.json`
    (9 models, 5 before); connecting GitHub wrote nothing locally (the
    connection is held by the ChatGPT account on the server).
  - Then (15:38Z to 15:46Z) the user installed the standalone Codex CLI
    beside the app with OpenAI's PowerShell installer for Windows (the
    exact command was not recorded; its layout is in
    [`collectors/research/codex-cli.md`](../../collectors/research/codex-cli.md))
    and gave it one prompt from a PowerShell console in a new folder
    `~\demo-cli`. The CLI shared `~\.codex` and the app's login: no
    second credential file appeared. Its rollout
    (`rollout-2026-10-15T11-41-45-<uuid>.jsonl`, 106,200 bytes, 47 lines:
    `session_meta` 1, `turn_context` 1, `world_state` 1, `response_item`
    20, `event_msg` 18, `token_usage_record` 6, 0 bad lines) names
    `originator` `codex-tui`, `cli_version` `0.162.1`, and `source`
    `vscode`, as the desktop app's do; its `session_meta.payload` has
    the same keys as the desktop rollouts, `creator_user_id` and
    `creator_account_id` included. The parser gave 31 rows: 2 `user`, 2
    `assistant`, 9 tool calls with their results (`exec` 5,
    `node_repl.js` 2, `shell` 1, `apply_patch` 1; `node_repl.js` is a
    tool of the `node_repl` MCP (Model Context Protocol) server the
    app's `config.toml` configures), `task_started` 15:42:43Z to
    `task_complete` 15:43:59Z (75,943 ms), `model: gpt-6.1-sol` (a third
    model id), and a `permission mode:` row with the granular approval
    object (`request_permissions` and `mcp_elicitations` true, the rest
    false) and the `workspace-write` sandbox. The sandbox failed to
    start a process during the run (`.sandbox/setup_error.json` `code`
    `helper_unknown_error`), so some tool calls failed. The CLI also
    wrote `history.jsonl`, which the desktop app had not: one line with
    `session_id`, `text` and `ts`, the shape of
    [section 5](#5-other-files). The console commands that started it
    are in PowerShell's own history file, which is shell history and
    left to the EDR.
  - Not exercised: a resumed thread, a denied tool call, an "allow
    always" grant, a model switch within a thread, subagents, an
    automation run. The macOS round of 2026-10-18 below exercised all
    of them but the grant and a subagent the agent spawned itself.
- **Observed (macOS)**: the author's macOS lab VM, macOS 26.6.2 (build
  25G83), arm64, one user, 2026-10-15, 16:25Z to 17:05Z (times in UTC;
  issues 118 and 121), read for file names, sizes, key names, value
  types and row counts only. The user repeated the Windows round: the
  ChatGPT app 26.1007.71326 (an Electron build, bundle identifier
  `com.openai.codex`; its own files are in
  [`collectors/research/chatgpt-desktop.md`](../../collectors/research/chatgpt-desktop.md)),
  with its bundled Codex reporting `originator` `Codex Desktop` and
  `cli_version` `0.162.0-alpha.17.2` as on Windows, then the standalone
  Codex CLI 0.162.1 from its shell installer. Both wrote the same
  `~/.codex` tree as on Windows.
  - Four rollouts under `sessions/2026/10/15/` (348 KB in all): a task
    in the project folder `~/Demo` (16:39Z to 16:40Z, Codex Desktop,
    model `gpt-6.1-sol`); the automation's target thread in
    `~/Documents/Codex/2026-10-15/new-chat` (16:44Z, Codex Desktop,
    `gpt-5.6-terra`); a thread in the projectless output directory
    `~/Documents/Codex/2026-10-15/e` (16:50Z, Codex Desktop,
    `gpt-6.1-sol`, with a `codex_app.load_workspace_dependencies` tool
    call; which user action it was is not determined); and the CLI's
    thread in `~/demo2` (16:55Z to 16:56Z, `originator` `codex-tui`,
    `cli_version` `0.162.1`, `gpt-6.1-sol`). The analyzer gave 91 rows
    in 4 sessions, each session start naming the account and user ids,
    plus the automation's `scheduled task:` row.
  - `automations/<slug>/automation.toml` (written 16:44:05Z) with the
    same keys as on Windows ([section 5](#5-other-files)), `rrule` of the
    form `FREQ=WEEKLY;BYHOUR=9;BYMINUTE=0;BYDAY=MO`, and one
    `sqlite/codex-dev.db` `automations` row; `automation_runs` empty.
    `local_thread_catalog` held 3 `vscode` rows and 3 `chatgpt` rows
    (two with `conversation_origin` null, one `tpp`): the ChatGPT chat
    and image generation again left no local transcript.
  - `history.jsonl` was written by the CLI, as on Windows.
  - `app-server-daemon/daemon.pid` (472 bytes) and `daemon-updater.pid`
    (194 bytes) carry a `processIdentity` object (`bootId` UUID,
    `startSeconds`, `startMicroseconds`, `uniqueId`) that the Windows
    files lack. The parser reads neither.
  - Not exercised: as on Windows.
- **Observed (macOS, 2026-10-18)**: the same macOS lab VM (macOS 26.6.2,
  build 25G83, arm64, one user), 2026-10-18 18:15Z to 2026-10-19
  00:43Z (issue 160, the resume and sync question, and issue 49, the
  ChatGPT desktop parser), read for file names, sizes, key names, value
  types, enum values and row counts only, with a listing diff after
  every step, so each file below is mapped to the step that wrote it.
  The ChatGPT app was build 26.1013.40934 (bundle identifier
  `com.openai.codex`, the build after the 26.1007.71326 of the
  2026-10-15 round), its bundled Codex reporting `originator`
  `Codex Desktop` and `cli_version` `0.163.0-alpha.10.2` (0.162.0-alpha.17.2
  on 2026-10-15). The app's own files are in
  [`collectors/research/chatgpt-desktop.md`](../../collectors/research/chatgpt-desktop.md).
  Times are UTC. The listings of the first five steps (install to the
  approvals) were taken in the VM's local zone, Eastern Daylight Time
  (UTC-4), and are converted here. Rollout file names and their date
  directories are in local time too, as [section 2](#2-transcript-files)
  says from source: the plain question's rollout is named
  `rollout-2026-10-18T14-40-09-<uuid>.jsonl` for a thread that
  started at 18:40:09Z. The parser takes every time from the records,
  never from the file name (a research note, no parser change).
  Terms used below, as the app names them in build 26.1013.40934
  (2026-10-18): the composer (the prompt box) has a mode dropdown with
  **Codex** and **ChatGPT**; Codex mode starts a local Codex thread
  with a rollout, and the ChatGPT entry lists the account's
  conversations on chatgpt.com. Every thread of this round was created
  in Codex mode; which mode the plain chats of the 2026-10-15 rounds
  used, which left no rollout, was not recorded. The **app server** is
  Codex's local service that owns the threads; the desktop app and any
  paired phone are its clients, and each request they send is logged
  in `logs_2.sqlite` under a method name such as `thread/start`,
  `thread/resume` or `turn/start` (a remote procedure call, RPC below).
  - Install (the app first launched 18:17:26Z) and sign-in
    (18:31:28Z to 18:32:34Z). Before sign-in `~/.codex` held
    `config.toml`, `.codex-global-state.json`, `installation_id`,
    `state_5.sqlite` (every table empty but `thread_sections` 1 and
    the bookkeeping tables), `logs_2.sqlite` (1,000 rows),
    `goals_1.sqlite`, `memories_1.sqlite`, `queue_1.sqlite` and
    `sqlite/codex-dev.db`; no `auth.json`, no `sessions/`, no
    `history.jsonl`. Sign-in wrote `auth.json`, `models_cache.json`
    (9 models), the first `shell_snapshots/<uuid>.<ns>.sh`
    ([section 5](#5-other-files)) and, in `codex-dev.db`
    `local_thread_catalog`, three `source_kind` `chatgpt` rows before
    any chat on this VM: the account's conversations, dated 2026-10-15
    (the Windows round's chat and image generation on the same
    account), each with `display_title` set, `conversation_origin`
    empty twice and `tpp` once, and `thread_source`, `model_provider`,
    `cwd`, `git_branch`, `project_id` and `chatgpt_async_status`
    null. The
    2026-10-15 macOS round's chats were not among them; why was not
    determined. `logs_2.sqlite` `logs.ts` is integer epoch seconds.
  - A plain question in Codex mode, no tools (18:40:09Z to
    18:40:31Z): one rollout, `sessions/2026/10/18/rollout-...`,
    190,766 bytes, 21 lines: `session_meta` 1, `event_msg` 6
    (`task_started`, `thread_settings_applied`, `item_completed` 2,
    `token_count`, `task_complete`), `response_item` 11
    (`additional_tools` 1, `message` with role `developer` 6, `user` 3,
    `assistant` 1), `world_state` 1, `turn_context` 1,
    `token_usage_record` 1, 0 bad lines. Its `cwd` was
    `~/Documents/Codex/2026-10-18/w`, the app's projectless output
    directory: the directory the app creates under
    `~/Documents/Codex/<date>/` for a thread that belongs to no
    project, with `work` and `outputs` inside. The app wrote no
    `history.jsonl` and no `version.json`; the prompt went to the
    `prompt-history` key of `.codex-global-state.json`
    ([section 5](#5-other-files)). `session_index.jsonl` got 1 line,
    `thread_history_1.sqlite` was created (`thread_items` 2,
    `thread_turns` 1), `state_5.sqlite` `threads` got 1 row and
    `codex-dev.db` `local_thread_catalog` a `vscode` row with
    `thread_source` `user` and the `cwd`.
  - `session_meta.payload` keys as on Windows (`source` `vscode`,
    `thread_source` `user`, `history_mode` `paginated`,
    `model_provider` `openai`, `creator_account_id` a UUID,
    `creator_user_id` 29 characters, `context_window` with
    `window_id`, `runtime_workspace_roots` 1 entry,
    `base_instructions` with `text` of 21,769 characters and
    `provenance`). The guardian review thread below adds
    `parent_thread_id` (absent on user threads) and
    `multi_agent_version` `disabled`.
  - `turn_context.payload` keys beyond the source list: `model`
    `gpt-6.1-sol`, `effort` `low`, `collaboration_mode` (`mode`
    `default`, `settings` with `model`, `reasoning_effort` and
    `developer_instructions` of 1,288 characters), `approval_policy`
    the granular object (`mcp_elicitations`, `request_permissions`,
    `rules`, `sandbox_approval`, `skill_approval`) in the first thread
    and the string `on-request` in later ones, `approvals_reviewer`
    `user`, `active_permission_profile` (`id`), `permission_profile`
    (`type` `managed`, `file_system` restricted, `network` restricted),
    `sandbox_policy` (`type` `workspace-write`, `writable_roots` 2,
    `network_access`, `exclude_slash_tmp`, `exclude_tmpdir_env_var`),
    `file_system_sandbox_policy` (`kind` `restricted`, 18 `entries`),
    `cyber_access_program` `standard`, `multi_agent_version` `v2`,
    `realtime_active`, `disabled_plugin_ids` (empty).
  - `world_state` keys: `tools` (the `mcp__codex_apps__*` tools
    `github`, `pets`, `hotline`, `sites`, `search_service`,
    `safety_settings`, `plugin_management` and
    `codex_document_control`, plus `mcp__code_review` and
    `mcp__node_repl`), `top_level_tools` (`clock.*`,
    `collaboration.*` with `spawn_agent` and `send_message`,
    `functions.exec`, `functions.request_user_input`,
    `functions.wait`, `mcp__cua_repl.*`), `permissions`
    (`approved_command_prefixes`, `instructions`), `environments`
    (`current_date`, `timezone`, `filesystem`), `host_skills`,
    `multi_agent_mode` (`mode` `explicitRequestOnly`),
    `git_attribution`. Messages carry
    `internal_chat_message_metadata_passthrough`; the line `metadata`
    keys are `client_authored`, `mcp_attribution`, `retained_source`
    and `user_input_order`; the assistant message has `phase` and
    `status`.
  - A coding task in a project (`~/Demo` added through the folder
    picker 18:48:52Z; thread 18:49:06Z to 18:50:51Z). Adding the
    project wrote `[projects."<path>"] trust_level = "trusted"` to
    `config.toml` (a trusted-folder grant, standing permission state)
    and a `projects` and a `project_roots` row to `state_5.sqlite`.
    The rollout (205,378 bytes, 39 lines): `session_meta` 1,
    `turn_context` 1, `world_state` 1, `response_item` 18 (developer 6,
    user 3, assistant 2, `additional_tools` 1, `custom_tool_call` 3
    with `call_id`, `id`, `input`, `name`, `status`,
    `custom_tool_call_output` 3), `event_msg` 14 (`item_completed` 7:
    `CommandExecution` 3, one `failed` with `exit_code` 1, keys `id`,
    `process_id`, `cwd`, `parsed_cmd`, `source`, `status`,
    `aggregated_output`, `exit_code`, `duration` with `secs` and
    `nanos`; `FileChange` 1, its `changes` keyed by the three absolute
    paths, `status` `completed`, `stdout`, `stderr`; `AgentMessage` 2
    with `phase` `commentary`; `UserMessage` 1 with `client_id`,
    `content`, `id`; then `token_count` 4, `task_started`,
    `thread_settings_applied`, `task_complete`), `token_usage_record`
    4. No approval event: the sandbox allowed the three writes inside
    the workspace. No `git` block (`~/Demo` is not a repository), and
    no file was written inside the project but the three the task
    made. `thread_history_1.sqlite` `item_json` keys:
    `userMessage` (`clientId`, `content`, `id`, `text`,
    `text_elements`, `type`), `agentMessage` (`delivery`, `id`,
    `memoryCitation`, `phase`, `questions`, `text`, `type`),
    `commandExecution` (`aggregatedOutput`, `command`,
    `commandActions`, `cwd`, `durationMs`, `exitCode`, `id`,
    `pluginId`, `processId`, `scriptPath`, `source`, `status`,
    `type`), `fileChange` (`changes`, `diff`, `id`, `kind`, `path`,
    `status`, `type`).
  - One tool call denied and one approved in the Demo thread (turns
    19:03:50Z to 19:04:04Z and 19:04:46Z to 19:05:03Z). A `curl` ran
    in the sandbox first and failed (`exit_code` 6, the network
    sandbox: `network_access` false); the agent asked to run it
    outside the sandbox, the user declined in the approval dialog,
    and the second call's output was the text `Script error:
    exec_command failed: CreateProcess { message: "Rejected(\"rejected
    by user\")" }` (in `thread_history_1.sqlite` a `commandExecution`
    `failed`, exit 1). The approved call wrote a file on the Desktop
    (`CommandExecution` `completed`, exit 0). The rollout holds no
    approval or decision event and `turn_context` did not change;
    the decisions are only in `logs_2.sqlite`
    ([section 5](#5-other-files)): the app server's response rows
    `CommandExecutionRequestApproval` with `decision: Decline` at
    19:04:01Z and `decision: Accept` at 19:05:00Z, and in the same
    seconds the core's `ExecApproval` rows with `decision: denied` and
    `decision: approved`, which are the ones still in the database at
    collection time. The dialog of build 26.1013.40934 offered no "always
    allow" choice for a command, and the approval was one-off: the
    thread's standing permissions in the global state kept one
    writable root. `task_started.turn_attribution` keys: `turn_id`,
    `turn_trigger` (`composer` for a prompt typed in the app),
    `parent_turn_id`, `initiating_agent_path`, `root_turn_id`.
    `token_count.rate_limits` keys: `limit_id` (`codex`), `plan_type`
    (`plus`), `primary`, `secondary`, `credits`, `limit_name`,
    `individual_limit`, `spend_control_reached`,
    `rate_limit_reached_type`, so every rollout names the account's
    plan.
  - A model switch and the **Approve for me** mode in the Demo
    thread (21:25:09Z and 21:25:28Z), then one prompt (21:26:40Z to
    21:27:32Z). Approve for me is a permission mode of build
    26.1013.40934 (2026-10-18) that hands each approval request to an
    automatic reviewer instead of asking the user; Codex calls the
    reviewer the guardian (`thread_source` `guardian_review`) and the
    mode auto-review (`approvals_reviewer` `auto_review`), and the
    app's global state calls it `guardian-approvals`. The switch alone,
    before any prompt, appended `event_msg` `thread_settings_applied`
    with `thread_settings.model` `gpt-5.6-terra` (the three earlier
    ones said `gpt-6.1-sol`); the mode change appended a second one
    with `approvals_reviewer` `user` -> `auto_review`, `approval_policy`
    still `on-request`, `permission_profile` `managed` and
    `active_permission_profile` `id` `:workspace`; a third, identical,
    preceded the turn. The event's full key set has 14 keys:
    `active_permission_profile`, `approval_policy`,
    `approvals_reviewer`, `collaboration_mode`, `cwd`,
    `disabled_plugin_ids`, `model`, `model_provider_id`,
    `permission_profile`, `personality`, `reasoning_effort`,
    `reasoning_summary`, `runtime_workspace_roots`, `service_tier`;
    it has no `sandbox_policy`. The next `turn_context` (21:26:41Z)
    said `gpt-5.6-terra` and `auto_review`, and
    `task_started.model_context_window` went from 475000 to 258400.
    `state_5.sqlite` `threads.model` was overwritten with the new
    model, so the switch history is only in the rollout and
    `logs_2.sqlite`. The config file did not change: the mode is kept
    in the global state, not in `config.toml`. The agent wrote the
    requested file to `~/Documents`, not to the Desktop as asked
    (build 26.1013.40934).
  - The guardian review thread. When the turn's command wrote outside
    the workspace, no dialog appeared; the app started a second
    thread with its own rollout (105,545 bytes, 17 lines:
    `session_meta`, `task_started`, 5 `response_item`, `world_state`,
    `turn_context`, `thread_settings_applied`, `item_completed`
    `Reasoning` and `AgentMessage`, `token_usage_record`,
    `token_count`, `task_complete`). Its `session_meta` has `source`
    `{"subagent": {"other": "guardian"}}`, `thread_source`
    `guardian_review`, `parent_thread_id` the Demo thread, the same
    `cwd` and two `runtime_workspace_roots`; its `turn_context` has
    `model` `codex-auto-review`, `approval_policy` `never`,
    `approvals_reviewer` `auto_review`, `sandbox_policy` `read-only`;
    `turn_attribution.turn_trigger` is `guardian_review`.
    `task_complete.last_agent_message` (and the `AgentMessage`) is a
    JSON string with `risk_level` (`low`), `user_authorization`
    (`high`), `outcome` (`allow`) and `rationale` (free text): the
    automatic decision for the call. The parent rollout then shows the
    `FileChange` completing at 21:27:27Z with no approval event of
    its own. `logs_2.sqlite` joins the two ([section 5](#5-other-files)).
    The reviewer thread has a `state_5.sqlite` `threads` row
    (`thread_source` `guardian_review`, `model` `codex-auto-review`,
    `approval_mode` `never`, `has_user_event` 0), items in
    `thread_history_1.sqlite` and a `session_index.jsonl` line named
    `Guardian review`, but no `thread_spawn_edges` row. This turn also
    had the first `item_completed` `Extension` items with `kind`
    `web.search` (keys `action`, `id`, `kind`, `query`, `results`,
    `type`) and `Reasoning` items (`id`, `raw_content`,
    `summary_text`).
  - A resumed thread: the app quit about 21:38Z to 21:40Z, relaunched
    21:45:36Z, the Demo thread reopened 21:46:06Z and given one prompt
    (21:47:36Z to 21:47:45Z). The resume appended to the same rollout:
    no new file, no second `session_meta`, no resume event. Opening the
    thread appended a `thread_settings_applied` with 11 keys (the 14
    less `personality`, `reasoning_summary` and `service_tier`) at
    21:46:11Z, which is the only resume mark in the rollout; the model
    switch and Approve for me survived the restart. `logs_2.sqlite`
    has the `thread/resume` requests at 21:46:06Z and 21:46:11Z, with
    `app_server.client_name` `Codex Desktop` and
    `app_server.client_version` `26.1013.40934`. The resume also
    started a prewarmed reviewer: a guardian session warmed up in
    advance that was not needed, which left a 0-byte
    `thread-writer-locks/<uuid>.lock` and nothing else
    ([section 5](#5-other-files)).
  - A **Full access** turn: Full access is the app's access level of
    build 26.1013.40934 (2026-10-18) that runs commands with no sandbox
    and no approvals. Setting it (21:52:30Z) appended a
    `thread_settings_applied` with `approval_policy` `never`,
    `approvals_reviewer` `user`, `active_permission_profile` `id`
    `:danger-full-access` and `permission_profile` `{"type":
    "disabled"}`; the turn's `turn_context` (21:53:27Z) adds
    `sandbox_policy` `danger-full-access` and
    `file_system_sandbox_policy` null. The user set it back by hand
    at 21:53:38Z, 5 seconds after the turn, which appended another
    `thread_settings_applied` with the earlier values (`on-request`,
    `auto_review`, `:workspace`, `managed`): the app does not turn Full
    access off by itself, and it stays a thread setting until changed. `state_5.sqlite`
    `threads.approval_mode` and the global state keep only the
    reverted value, so the full-access turn is recorded only in the
    rollout and `logs_2.sqlite`.
  - A reply to an existing ChatGPT conversation in ChatGPT mode
    (about 22:02Z to 22:15Z) wrote nothing to the Codex stores: no
    rollout, no index line, no database growth, and the three
    `chatgpt` catalog rows kept their 2026-10-15 update times. The
    conversation never passed through the app server. On chatgpt.com
    the Codex area did not list the app's local threads (user report,
    no listing).
  - A scheduled task, created in the sidebar's Scheduled view
    (23:18:38Z) on a daily schedule, run once with Run now
    (23:19:26Z to 23:19:30Z) and once on schedule (23:45:49Z to
    23:45:53Z). The app calls this kind of task a heartbeat
    (`automation.toml` `kind` `heartbeat`): each run ends with a
    `<heartbeat>` block in which the model decides whether to notify
    the user. Creating it wrote `automations/<slug>/automation.toml`
    and `automations/.run-jitter-salt` ([section 5](#5-other-files))
    and at once a new thread with its rollout (42 lines after Run now,
    62 after the scheduled run), whose `session_meta` says nothing
    about an automation (`source` `vscode`, `thread_source` `user`,
    `cwd` `~/Documents/Codex/2026-10-18/new-chat`). Only
    `turn_attribution.turn_trigger` marks the turns:
    `scheduled_task_setup` for the setup turn (the agent acknowledges
    the schedule, no tool call), `automation_heartbeat_run_now` for
    Run now, `automation_heartbeat_scheduled` for the scheduled run;
    the two runs' user messages have no `client_id`. The scheduled run's
    `task_complete.last_agent_message` ends in a `<heartbeat>` block
    with `<decision>DONT_NOTIFY</decision>` and a `<message>`, and the
    Run now report ends in a `<heartbeat>` block with an
    `<automation_id>`. Both runs reported into the same thread, the
    file's `target_thread_id`. The vendor page
    [Scheduled tasks | ChatGPT Learn](https://learn.chatgpt.com/docs/automations)
    (read 2026-10-18) says "Standalone scheduled tasks start a new
    chat for each scheduled run and report results in **Scheduled**";
    neither run here started a new chat. `automation_runs` and
    `inbox_items` stayed empty after both runs (a `NOTIFY` decision was
    not observed).
    A second prewarmed reviewer lock appeared at creation.
  - Remote control: the app's Settings > Connections > Control this
    Mac or PC, which pairs a phone (the ChatGPT app on iOS or
    Android) with the desktop so that the phone can drive the Mac's
    app server through OpenAI's relay. The vendor page
    [Remote connections | ChatGPT Learn](https://learn.chatgpt.com/docs/remote-connections)
    (read 2026-10-18) says "Remote connections let you access work
    running on another device or machine", "Your phone sends prompts,
    approvals, and follow-up messages to ChatGPT" and "Repository files
    and local documents come from the connected host"; it does not say
    whether a transcript is copied to the account. Enabling it
    (23:50:17Z) wrote one `state_5.sqlite` `remote_control_enrollments`
    row ([section 5](#5-other-files)) and two top-level global-state
    keys; pairing alone changed no rollout. One prompt from the iPhone
    (23:59:14Z to 23:59:31Z) and one from an Android phone (2026-10-19
    00:29:14Z to 00:29:16Z) appended ordinary turns to the Demo
    rollout, `turn_trigger` `remote_ios` and `remote_android`, with
    `turn_context` in the shape of a composer turn; the trigger is the
    only mark in the rollout that a turn came from a phone. In
    `logs_2.sqlite` each phone is a second app-server connection with
    `app_server.client_name` `codex_chatgpt_ios_remote` (version
    `1.2026.279`) or `codex_chatgpt_android_remote` (version `dev`);
    besides `turn/start` the phones sent `command/exec` (a command run
    on the host outside any turn), `fs/readFile` and
    `gitDiffToRemote`. Turning "Allow connections" off (00:05:42Z) and
    on (00:09:25Z) flipped `remote_control_enabled` in the same row;
    revoking the iPhone (00:14:36Z) and pairing the Android phone
    (00:23:10Z) wrote only log rows. The full `turn_trigger` set of
    this build: `composer`, `remote_ios`, `remote_android`,
    `guardian_review`, `scheduled_task_setup`,
    `automation_heartbeat_run_now`, `automation_heartbeat_scheduled`.
  - The plain-question thread deleted with the app's own delete
    command (2026-10-19 00:36:02Z; the dialog mentioned no remote
    copy). Removed: the rollout (no `archived_sessions/` exists: a
    hard delete, not an archive), its `session_index.jsonl` line, its
    `state_5.sqlite` `threads` and `thread_read_receipts` rows, its
    `thread_history_1.sqlite` rows and its `codex-dev.db`
    `local_thread_catalog` row; `logs_2.sqlite` has `fs/remove` and
    `thread/delete` requests at that second. Survived: the global
    state keys that name the thread (its `prompt-history` entry with
    the prompts, `thread-descriptions-v1`,
    `thread-user-activity-times-v1`,
    `heartbeat-thread-permissions-by-id`, `client-thread-bindings-v1`,
    the top-level `projectless-thread-ids`,
    `thread-projectless-output-directories` and
    `thread-workspace-root-hints`) plus a new key
    `codex-writing-block-deleted-thread-v1:<uuid>` set to true, the
    deletion marker; the empty projectless output directory
    `~/Documents/Codex/2026-10-18/w`; and at least one
    `logs_2.sqlite` row carrying the thread id.
  - Collector 1.14.0 ran in the VM as the user (2026-10-19 00:43:01Z
    to 00:43:21Z) and analyzer 0.15.0 over its archive. Every
    `~/.codex` file, `codex-dev.db`, `logs_2.sqlite`, the global state
    and `automations/` included, is attributed to `codex-cli` by the
    `codex-cli|.codex` catalog line. The analyzer gave 182 rows in 3
    sessions (`assistant` 19, `system` 80, `tool_result` 36,
    `tool_use` 36, `user` 11), dropped 92 rows repeated by the
    secondary sources, and gave 0 `parser:` rows: the Demo thread (8
    user turns, models `gpt-6.1-sol` and `gpt-5.6-terra`), the
    guardian thread (0 user turns, `codex-auto-review`) and the
    scheduled task's thread (3 user turns), with 3 `thread record:`
    rows and 1 `scheduled task:` row. It already gave the session
    start, `model:` rows with the switch, `permission mode:` rows with
    the full-access transition, `subagent <id> of <parent>` for the
    guardian thread, and event times rather than file-name times. It
    dated the model switch and the full-access revert at the next
    `turn_context` instead of the settings event, did not show the
    Approve for me change, and gave no permission decision, turn
    trigger, remote-control or deleted-thread row. Since this round
    the parser reads those records ([section 8](#8-parser-plan-the-existing-parser)):
    `thread_settings_applied` for the model and permission mode, with
    the reviewer and profile id in the composite; the user decisions
    in `logs_2.sqlite` and the guardian verdicts; a `turn trigger:` row
    after each `task_started`; the `remote_control_enrollments` row; and the
    global state as a secondary source, which recovers the deleted
    thread's prompts and its deletion.
  - Research notes, no parser change: a `thread-writer-locks` lock can
    exist for a thread that has no rollout, `threads` row or index
    line (the prewarmed reviewers), so a lock is never a session; and
    rollout file names are in local time, which the parser never
    reads for a time.
  - Exercised here for the first time on any platform: a resumed
    thread, a denied and an approved tool call, a model switch within
    a thread, an automatic approval, scheduled-task runs, remote
    control and a delete. Not exercised: an "always allow" grant
    (build 26.1013.40934 offered none for a command), a subagent the
    agent spawned itself, a heartbeat `NOTIFY` decision, an
    `automation_runs` row, an archived thread.
- **Observed (Ubuntu)**: the author's Ubuntu 26.04.1 LTS lab VM, aarch64,
  kernel 7.0.0-38-generic, one user, 2026-10-15, 17:12Z to 17:22Z (times
  in UTC; issue 118), read for file names, sizes, key names, value types
  and line counts only. The user installed the standalone Codex CLI
  0.162.1 with its shell installer (no ChatGPT app exists for Linux),
  logged in through the browser flow and ran two turns in `~/demo`. The
  install layout is in
  [`collectors/research/codex-cli.md`](../../collectors/research/codex-cli.md).
  - One rollout, `sessions/2026/10/15/rollout-2026-10-15T13-16-43-<uuid>.jsonl`
    (440,924 bytes, 108 lines: `session_meta` 1, `turn_context` 2, one
    per turn, `world_state` 1, `response_item` 41, `event_msg` 49,
    `token_usage_record` 14, 0 bad lines), `originator` `codex-tui`,
    `cli_version` `0.162.1`, `source` `vscode`, `thread_source` `user`,
    the granular approval object, model `gpt-6.1-sol`. The turns wrote
    seven files into `~/demo`.
  - The analyzer gave 78 rows: 4 `user` (the two prompts from the
    rollout and the same two from `history.jsonl`), 7 `assistant`, 28
    tool calls with their results (`exec` 11, `shell` 8, `web_search` 8,
    and one `request_user_input_async`, a tool name not seen on the
    other platforms: the CLI asking the user a question mid-turn),
    `task_started` and `task_complete` for both turns (62,724 ms and
    43,305 ms), and the `model:` and `permission mode:` rows.
  - `history.jsonl` (370 bytes) held 2 lines, one per turn, with
    `session_id`, `text` and `ts`. There was no `sqlite/codex-dev.db`,
    no `automations/` and no `.codex-global-state.json`: those are the
    desktop app's.
  - `app-server-daemon/daemon.pid` (423 bytes) and `daemon-updater.pid`
    (145 bytes) carry `processIdentity` with `bootId` and `startTicks`
    on Linux, against `startSeconds`, `startMicroseconds` and `uniqueId`
    on macOS and no `processIdentity` on Windows. The parser reads
    neither.

## 2. Transcript files

Paths relative to the home; `$CODEX_HOME` replaces `.codex` when set.

- `.codex/sessions/YYYY/MM/DD/rollout-<YYYY-MM-DDThh-mm-ss>-<thread id>.jsonl`,
  one per thread, the directory date and file-name time in **local** time
  ([rollout/src/recorder.rs:1722-1734](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/rollout/src/recorder.rs#L1722-L1734),
  [rollout_file_name.rs:62-73](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/rollout/src/rollout_file_name.rs#L62-L73)).
  `thread/revert` writes a new file `rollout-<time>-<thread id>_<rollout id>.jsonl`
  that keeps the thread id and points back at its prefix
  ([recorder.rs:95-104](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/rollout/src/recorder.rs#L95-L104),
  [rollout_file_name.rs:40-47](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/rollout/src/rollout_file_name.rs#L40-L47)).
  Subagent threads get their own rollout in the same tree. **Parser reads.**
- `.codex/archived_sessions/`, same layout
  ([rollout/src/lib.rs:86-87](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/rollout/src/lib.rs#L86-L87)). **Parser reads.**
- `*.jsonl.zst`: zstd level 3, written by a background worker for rollouts
  idle seven days, in both trees
  ([compression.rs:29](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/rollout/src/compression.rs#L29),
  [362-363](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/rollout/src/compression.rs#L362-L363),
  [500-501](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/rollout/src/compression.rs#L500-L501)).
  The worker runs only with the `local_thread_store_compression` feature,
  which is under development and off by default
  ([features/src/lib.rs:1212-1217](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/features/src/lib.rs#L1212-L1217),
  [core/src/thread_manager.rs:461-503](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/core/src/thread_manager.rs#L461-L503)). **Parser reads** (needs `zstandard`).
- `.codex/history.jsonl`: one line per submitted prompt, all threads
  ([section 5](#5-other-files)). **Parser reads.**
- `.codex/session_index.jsonl`: thread renames ([section 5](#5-other-files)). Not read.
- `.codex/automations/<slug>/automation.toml`: a scheduled automation of
  the ChatGPT desktop app ([section 5](#5-other-files)). **Parser reads.**
- `.codex/state_5.sqlite`, `.codex/thread_history_1.sqlite`: thread metadata
  and a projection of paginated rollouts ([section 5](#5-other-files)).
  **Parser reads**, as secondary sources (issue 122).

## 3. Record envelope and types

Each line is a `RolloutLine`: `timestamp`, optional `ordinal`, and the item
flattened beside them
([history/src/lib.rs:356-367](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/history/src/lib.rs#L356-L367),
[recorder.rs:2062-2091](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/rollout/src/recorder.rs#L2062-L2091)).
The item serialises as `{"type": <snake_case variant>, "payload": {...}}`;
`response_item` lines may also carry a sibling `metadata` object
([history/src/rollout_payload.rs:30-72](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/history/src/rollout_payload.rs#L30-L72)).
Codex's own reader requires `timestamp` and treats `ordinal` as optional
([rollout/src/lib.rs:52-74](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/rollout/src/lib.rs#L52-L74)).
`ordinal` is written only in paginated rollouts, counting from 0 or from the
`history_base` the file continues
([rollout/src/ordinal.rs:22-44](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/rollout/src/ordinal.rs#L22-L44)).

Line types ([history/src/lib.rs:209-227](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/history/src/lib.rs#L209-L227));
which ones are written is decided in
[rollout/src/policy.rs:22-50](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/rollout/src/policy.rs#L22-L50):

| `type` | `payload` | Seen locally |
| --- | --- | --- |
| `session_meta` | thread header, below | yes |
| `turn_context` | per-turn settings, below | yes |
| `response_item` | a Responses API item ([section 4](#4-message-content-and-tool-calls)) | yes |
| `event_msg` | a UI event, tagged by its own `type` (below) | yes |
| `token_usage_record` | `thread_id`, `turn_id`, `session_id`, `root_turn_id`, `response_id`, `usage`, `turn_token_usage`, `thread_token_usage` ([protocol.rs:2263-2273](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/protocol.rs#L2263-L2273)) | yes |
| `world_state` | `full`, `state` (model-visible environment snapshot or patch, [protocol.rs:3272-3278](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/protocol.rs#L3272-L3278)) | yes |
| `compacted` | `message` (the compaction summary), `replacement_history`, window ids ([history/src/lib.rs:285-306](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/history/src/lib.rs#L285-L306), [rollout_payload.rs:238-266](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/history/src/rollout_payload.rs#L238-L266)) | no |
| `inter_agent_communication` | `author`, `recipient`, `other_recipients`, `content` (plain text), `encrypted_content`, `trigger_turn` ([protocol.rs:806-822](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/protocol.rs#L806-L822)) | no |
| `inter_agent_communication_metadata` | `trigger_turn` | no |
| `retained_context` | verified answers and delivered messages for the guardian reviewer ([history/src/retained_context.rs:145-162](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/history/src/retained_context.rs#L145-L162)) | no |
| `security_risk_score` | `scores`, `call_id`, `action`, `sampled_at` ([security_risk.rs:12-25](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/security_risk.rs#L12-L25)) | no |
| `realtime_item` | `id`, `realtime_session_id`, tagged content incl. `transcript_segment` (`role`, `text`); paginated only ([realtime.rs:6-31](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/realtime.rs#L6-L31)) | no |

**`session_meta`** (line 1;
[protocol.rs:3117-3198](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/protocol.rs#L3117-L3198)):
`id` (this thread), `session_id` (the root thread's id; filled from `id`
when absent in old files,
[3243-3269](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/protocol.rs#L3243-L3269)),
`forked_from_id`, `parent_thread_id`, `timestamp`, `cwd`,
`runtime_workspace_roots`, `originator` (`codex-tui` locally), `cli_version`,
`source` (`cli`, `vscode`, `exec`, `mcp`, a custom string, or
`{"subagent": ...}`; [2824-2837](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/protocol.rs#L2824-L2837), [2905-2923](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/protocol.rs#L2905-L2923)),
`thread_source` (`user`, `subagent`, `guardian_review`,
`memory_consolidation` or a feature name; [2843-2849](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/protocol.rs#L2843-L2849)),
`agent_nickname`, `agent_role`, `agent_path`, `model_provider`,
`base_instructions`, `dynamic_tools`, `memory_mode`, `history_mode`
(`legacy` or `paginated`), `history_base`, `context_window`, and the account
fields `creator_user_id`, `creator_account_id`. Beside them, `git`
(`commit_hash`, `branch`, `repository_url`;
[3436-3452](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/protocol.rs#L3436-L3452)) is written only when `cwd` is inside a
git repository
([recorder.rs:1978-1990](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/rollout/src/recorder.rs#L1978-L1990)).

**`turn_context`** (once per user turn and after mid-turn compaction;
[protocol.rs:3296-3358](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/protocol.rs#L3296-L3358)):
`turn_id`, `root_turn_id`, `cwd`, `workspace_roots`, `current_date`,
`timezone`, `approval_policy`, `sandbox_policy`, `permission_profile`,
`network`, `model`, `collaboration_mode` (with its own `settings.model`),
`effort`, `summary`, `personality` and more. The four policy fields:
`approval_policy` is a kebab-case string, `untrusted`, `on-request` (the
default, also read from the old `on-failure`) or `never`, or an object
`{"granular": {...}}` for per-flow controls
([protocol.rs:986-1009](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/protocol.rs#L986-L1009));
`sandbox_policy` is an object tagged by `type`: `danger-full-access`,
`read-only`, `external-sandbox` or `workspace-write`, the last three
with fields of their own
([protocol.rs:1072-1120](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/protocol.rs#L1072-L1120));
`permission_profile`, optional, is an object tagged by `type`: `managed`
(`file_system`, `network`), `disabled` or `external` (`network`)
([models.rs:421-435](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/models.rs#L421-L435)); `network`,
optional, is `{allowed_domains, denied_domains}`, two lists of strings
([protocol.rs:3291-3294](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/protocol.rs#L3291-L3294)).

**`event_msg`** (tagged enum,
[protocol.rs:1352-1358](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/protocol.rs#L1352-L1358)). Persisted in every mode
([policy.rs:127-139](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/rollout/src/policy.rs#L127-L139)):
`task_started` (`turn_id`, `root_turn_id`, `trace_id`, `started_at` epoch
s, `model_context_window`, `collaboration_mode_kind`), `task_complete`
(`turn_id`, `last_agent_message`, `error`, `started_at`, `completed_at`,
`duration_ms`, `time_to_first_token_ms`)
([2152-2197](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/protocol.rs#L2152-L2197); the wire names
are kept from v1, [1407-1418](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/protocol.rs#L1407-L1418)),
`turn_aborted` (`turn_id`, `reason`, `error`, times;
[4243-4263](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/protocol.rs#L4243-L4263)),
`thread_rolled_back` (`num_turns`;
[3692-3696](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/protocol.rs#L3692-L3696)),
`token_count`, `thread_goal_updated`, `thread_settings_applied`, and
`item_completed` (below). Legacy-mode rollouts also keep `user_message`
(`message`, `images`), `agent_message` (`message`, `phase`),
`agent_reasoning` and `agent_reasoning_raw_content` (`text`),
`entered_review_mode`, `exited_review_mode`, `patch_apply_end`,
`context_compacted`, `mcp_tool_call_end`, `web_search_end`,
`image_generation_end` and `sub_agent_activity`
([policy.rs:141-158](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/rollout/src/policy.rs#L141-L158);
[protocol.rs:2518-2544](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/protocol.rs#L2518-L2544),
[2637-2645](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/protocol.rs#L2637-L2645)).
These repeat what the `response_item` lines carry.

`item_completed` (`thread_id`, `turn_id`, `item`, `started_at_ms`,
`completed_at_ms`;
[protocol.rs:1947-1960](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/protocol.rs#L1947-L1960))
carries a `TurnItem` tagged by PascalCase `type`: `UserMessage`,
`AgentMessage`, `Reasoning`, `CommandExecution` (`command`, `cwd`,
`aggregated_output`, `exit_code`, `duration`), `McpToolCall` (`server`,
`tool`, `arguments`, `result`), `FileChange` (`changes`, `stdout`,
`stderr`), `WebSearch`, `Extension` (`kind` `web.search`, `clock.sleep` or
`image_gen.generation`), `Plan`, `CollabAgentToolCall` (`prompt`, `model`,
receiver thread ids) and others
([items.rs:42-78](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/items.rs#L42-L78),
[243-281](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/items.rs#L243-L281),
[337-422](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/items.rs#L337-L422),
[443-486](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/items.rs#L443-L486);
[ext/items/src/lib.rs:32-45](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/ext/items/src/lib.rs#L32-L45)).
Paginated rollouts persist every completed item, with command output and
MCP results cut to 64 KiB; legacy rollouts keep only `FunctionCallOutput`,
`Plan`, `clock.sleep` and completed `SubAgentActivity` items
([policy.rs:16-19](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/rollout/src/policy.rs#L16-L19),
[227-283](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/rollout/src/policy.rs#L227-L283)).
Locally the paginated rollout held `UserMessage`, `Extension`
(`web.search`, with `query`, `action` and `results`) and `AgentMessage`
items.

Everything else on the `EventMsg` enum (deltas, begin events, approvals,
`exec_command_end`, errors, warnings) is transient and never written
([policy.rs:160-223](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/rollout/src/policy.rs#L160-L223)).

## 4. Message content and tool calls

`response_item.payload` is a `ResponseItem` tagged by snake_case `type`
([protocol/src/models.rs:1010-1256](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/models.rs#L1010-L1256));
all variants but `compaction_trigger` and unknown ones are written
([policy.rs:78-100](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/rollout/src/policy.rs#L78-L100)).
Most variants carry an optional `id` and
`internal_chat_message_metadata_passthrough` (`turn_id`, `create_time` in
fractional epoch seconds, `content_item_kinds`;
[models.rs:954-994](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/models.rs#L954-L994)).

- `message`: `role` (`user`, `assistant`, `developer`; the harness's own
  instructions go in as `developer`), `content[]` of `input_text`,
  `input_image` (`image_url` or `file_id`), `input_audio` or `output_text`
  blocks, each with `text` where textual
  ([876-896](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/models.rs#L876-L896)),
  and `phase` (`commentary` or `final_answer`;
  [938-952](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/models.rs#L938-L952), [1021-1036](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/models.rs#L1021-L1036)).
  A `role: "user"` message is not always typed by the user: the harness
  injects `AGENTS.md` instructions, `<environment_context>`, skill text,
  subagent notifications, turn-aborted notices and user shell commands as
  user-role messages
  ([core/src/context/contextual_user_message.rs:22-37](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/core/src/context/contextual_user_message.rs#L22-L37)).
  Current versions label each content block in
  `content_item_kinds`; typed input is `user.text`, the environment block
  `environments.environment_context`
  ([contextual_user_message.rs:51-82](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/core/src/context/contextual_user_message.rs#L51-L82),
  [core/src/context/world_state/environment.rs:200-203](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/core/src/context/world_state/environment.rs#L200-L203)).
  Locally the first turn had three `developer` messages and two `user`
  messages, of which one was `environments.environment_context` and one
  `user.text`.
- `reasoning`: `summary[]` of `summary_text` (`text`), `content[]` of
  `reasoning_text` or `text`, `encrypted_content`
  ([1048-1060](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/models.rs#L1048-L1060), [1982-1993](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/models.rs#L1982-L1993)).
  `content` is written only when it holds `reasoning_text` parts or is null
  ([1624-1631](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/models.rs#L1624-L1631)).
- `function_call`: `name`, `namespace` (MCP and plugin tools), `arguments`
  (a JSON **string**), `call_id`
  ([1074-1093](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/models.rs#L1074-L1093)).
- `custom_tool_call`: `status`, `call_id`, `name`, `namespace`, `input`
  (free text) ([1134-1151](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/models.rs#L1134-L1151)).
  Code mode's `exec` tool
  ([code-mode-protocol/src/lib.rs:52](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/code-mode-protocol/src/lib.rs#L52))
  and the freeform `apply_patch` arrive this way; the one local call was
  `exec`.
- `local_shell_call`: `call_id`, `status`, `action` (`type: "exec"`,
  `command` array, `timeout_ms`, `working_directory`, `env`, `user`)
  ([1061-1073](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/models.rs#L1061-L1073), [1937-1950](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/models.rs#L1937-L1950)).
- `function_call_output`, `custom_tool_call_output`: `call_id`, `name`,
  `output`, which is a string or an array of `input_text`, `input_image`,
  `input_audio`, `encrypted_content` items
  ([1114-1133](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/models.rs#L1114-L1133), [1155-1169](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/models.rs#L1155-L1169), [2096-2118](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/models.rs#L2096-L2118), [2250-2263](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/models.rs#L2250-L2263)).
  Locally an array of two `input_text` items.
- `web_search_call`: `status`, `action` (`search` with `query`/`queries`,
  `open_page` with `url`, `find_in_page` with `url`, `pattern`)
  ([1191-1204](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/models.rs#L1191-L1204), [1952-1980](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/models.rs#L1952-L1980)). No output item.
- `tool_search_call` (`call_id`, `execution`, `arguments` object) and
  `tool_search_output` (`call_id`, `status`, `tools[]`)
  ([1094-1108](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/models.rs#L1094-L1108), [1170-1182](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/models.rs#L1170-L1182)).
- `agent_message`: `author`, `recipient`, `content[]` of `input_text` or
  `encrypted_content` ([906-911](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/models.rs#L906-L911), [1037-1047](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/models.rs#L1037-L1047)).
- `image_generation_call`: `status`, `revised_prompt`, `result` (image data)
  ([1214-1226](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/models.rs#L1214-L1226)).
- `additional_tools` (tool definitions), `compaction` and
  `context_compaction` (`encrypted_content`), `configuration_update`: no
  readable conversation content
  ([1013-1020](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/models.rs#L1013-L1020), [1227-1253](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/models.rs#L1227-L1253)).

The `metadata` sibling on a `response_item` line is harness bookkeeping:
`client_authored`, `retained_source`, `user_input_order`,
`inherited_user_message` (copied from a parent thread), `mcp_attribution`
and others
([history/src/lib.rs:55-135](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/history/src/lib.rs#L55-L135)).

**Joins.** Tool call to result: `call_id`, equal on the call and its
`*_output`. Turn: `turn_id` on `turn_context`, `task_started`,
`task_complete`, `item_completed` and in each item's metadata passthrough.
An `item_completed` item that a code-mode `exec` call produced (the local
`web.search`) has its own id, not the call's `call_id`, so nothing joins it
to the call except its position between the call and its output (local).

## 5. Other files

- `history.jsonl`: `{session_id, ts, text}`, `ts` epoch **seconds**,
  `session_id` the thread id, one line per prompt typed into the TUI
  ([message-history/src/lib.rs:61-66](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/message-history/src/lib.rs#L61-L66),
  [127-138](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/message-history/src/lib.rs#L127-L138)).
  Written unless `history.persistence = "none"`
  ([config/src/types.rs:211-219](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/config/src/types.rs#L211-L219)); trimmed oldest-first when
  `history.max_bytes` is set
  ([message-history/src/lib.rs:191-195](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/message-history/src/lib.rs#L191-L195)). It can outlive the rollout it
  names (deleted or ephemeral threads), so it is the one place such a
  prompt survives. Local: one line, those three keys, 10-digit `ts`.
- `session_index.jsonl`: `{id, thread_name, updated_at}` appended per
  rename, newest wins, `updated_at` RFC 3339 UTC with nanoseconds
  ([rollout/src/session_index.rs:24-48](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/rollout/src/session_index.rs#L24-L48)). Titles only; local shape matches.
  Codex Desktop also lists the guardian review thread, as
  `Guardian review`, and a scheduled task's thread, under the task's
  name (macOS, build 26.1013.40934, 2026-10-18;
  [section 1](#1-evidence)). The app's delete removes the thread's line.
- `state_5.sqlite` `threads`: `id`, `rollout_path`, `created_at`, `cwd`,
  `title`, `git_sha`, `git_branch`, `git_origin_url` and later
  `first_user_message`, `preview`
  ([state/migrations/0001_threads.sql:1-19](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/state/migrations/0001_threads.sql#L1-L19),
  [0007_threads_first_user_message.sql:1](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/state/migrations/0007_threads_first_user_message.sql#L1),
  [0032_threads_preview.sql:1](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/state/migrations/0032_threads_preview.sql#L1)); `thread_spawn_edges`
  links parent and child threads
  ([0021_thread_spawn_edges.sql:1-5](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/state/migrations/0021_thread_spawn_edges.sql#L1-L5)). A row whose rollout is gone still holds the
  first prompt. The file name is fixed beside the other databases
  ([state/src/sqlite.rs:34-39](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/state/src/sqlite.rs#L34-L39)).
  The columns the parser reads (issue 122), each only when the table has
  it:
  - `id`, the thread id: the rollout's `session_meta.id`, so the rows join
    the rollout's on `session_id`.
  - `created_at` in epoch seconds and `created_at_ms` in epoch ms
    ([0025_thread_timestamps_millis.sql:1-2](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/state/migrations/0025_thread_timestamps_millis.sql#L1-L2)),
    both the thread's creation time
    ([state/src/runtime/threads.rs:666-670](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/state/src/runtime/threads.rs#L666-L670)).
  - `cwd`, `title`, `git_branch`, `rollout_path`, `archived`, `model` (the
    last turn's, set from each `turn_context`;
    [state/src/extract.rs:122-130](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/state/src/extract.rs#L122-L130)),
    `name` (a rename;
    [0041_threads_name.sql:1](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/state/migrations/0041_threads_name.sql#L1)),
    `source` and `thread_source`
    ([0030_threads_thread_source.sql:1](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/state/migrations/0030_threads_thread_source.sql#L1)).
  - `first_user_message`: the first `UserMessage` event's text, trimmed
    and with the `## My request for Codex:` prefix removed, or `[Image]`
    or `[Audio]` for a prompt with no text
    ([state/src/extract.rs:184-196](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/state/src/extract.rs#L184-L196),
    [protocol/src/protocol.rs:145-150](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/protocol.rs#L145-L150),
    [2614-2635](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/protocol.rs#L2614-L2635)). No column
    records when the prompt was typed: `created_at` is the thread's
    creation, which the TUI does before the first prompt.

  Not read: `sandbox_policy` and `approval_mode` (the latest
  `turn_context` policy, which the rollout's `permission mode:` rows
  already carry), `preview` (the first prompt again, or a thread goal's
  objective), the token and recency bookkeeping. What it survives: a
  rollout deleted, moved or truncated outside Codex, or excluded by the
  collector's size limit. Codex's own thread delete removes the rollout
  and the database rows together
  ([thread-store/src/local/delete_thread.rs:66-92](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/thread-store/src/local/delete_thread.rs#L66-L92)),
  so it survives no delete made in Codex. Whether a rollback or a revert
  rewrites `first_user_message` was not determined.
- `thread_history_1.sqlite`: `thread_turns`, `thread_items` (`item_json`,
  the app-server's camelCase `ThreadItem`), `thread_realtime_items`, keyed
  by `rollout_ordinal`
  ([state/thread_history_migrations/0001_thread_history.sql:1-38](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/state/thread_history_migrations/0001_thread_history.sql#L1-L38)).
  A projection of paginated rollouts; local item types were `userMessage`,
  `webSearch`, `agentMessage`, the same three items as the rollout's
  `item_completed` lines. Nothing found that is not in the rollout.
  Codex Desktop on Windows (observed 2026-10-15,
  [section 1](#1-evidence)) added `reasoning`, `commandExecution` and
  `fileChange` items, also all in its rollouts. Record shapes from source
  (issue 122):
  - What is projected: one rollout line at a time, `task_started`,
    `task_complete` and `turn_aborted` into `thread_turns` and each
    `item_completed` into `thread_items`; every other line type
    projects nothing
    ([app-server-protocol/src/protocol/thread_history_projection.rs:21-99](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/app-server-protocol/src/protocol/thread_history_projection.rs#L21-L99)).
    `history_mode` `legacy` rollouts are not projected
    ([line 1-4](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/app-server-protocol/src/protocol/thread_history_projection.rs#L1-L4)).
  - `thread_turns`: `status` `inProgress`, `completed`, `interrupted` or
    `failed`, `started_at` and `completed_at` in epoch seconds (the turn
    events' fields;
    [protocol/src/protocol.rs:2189-2192](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/protocol.rs#L2189-L2192)),
    `duration_ms`, `error_json`; `rollout_end_ordinal` from migration
    0003 ([0003_turn_rollout_positions.sql:1-3](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/state/thread_history_migrations/0003_turn_rollout_positions.sql#L1-L3);
    written at [thread-store/src/local/thread_history.rs:316-351](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/thread-store/src/local/thread_history.rs#L316-L351)).
    The two events are the rollout's `task_started` and `task_complete`
    lines ([protocol/src/protocol.rs:1407-1418](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/protocol.rs#L1407-L1418)).
  - `thread_items`: `created_at_ms` is the item's `started_at_ms`, or the
    rollout line's `timestamp` when the event has none
    ([thread_history.rs:431-438](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/thread-store/src/local/thread_history.rs#L431-L438),
    [thread_history_materialization.rs:245-252](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/thread-store/src/local/thread_history_materialization.rs#L245-L252));
    `started_at_ms` and `completed_at_ms` from migration 0007
    ([0007_thread_item_lifecycle_timestamps.sql:1-2](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/state/thread_history_migrations/0007_thread_item_lifecycle_timestamps.sql#L1-L2))
    are the `item_completed` event's, when the item started and when it
    completed
    ([core/src/session/mod.rs:2546-2601](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/core/src/session/mod.rs#L2546-L2601)).
    `item_type` is `item_json.type`
    ([0002_thread_items_item_type.sql:1-5](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/state/thread_history_migrations/0002_thread_items_item_type.sql#L1-L5)).
  - `item_json` is `ThreadItem`, tagged by `type` in camelCase
    ([app-server-protocol/src/protocol/v2/item.rs:232-429](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/app-server-protocol/src/protocol/v2/item.rs#L232-L429)),
    converted from the rollout's turn item
    ([869-1063](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/app-server-protocol/src/protocol/v2/item.rs#L869-L1063)):
    `userMessage` (`content[]` of `UserInput`, `text` inputs with
    `text`; [v2/turn.rs:425-459](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/app-server-protocol/src/protocol/v2/turn.rs#L425-L459)),
    `agentMessage` (`text`, the content blocks concatenated, `phase`),
    `reasoning` (`summary[]`, `content[]`, strings), `commandExecution`
    (`command` a display string, `cwd`, `status`, `aggregatedOutput`,
    `exitCode`, `durationMs`), `fileChange` (`changes[]` of `path`,
    `kind`, `diff`; [v2/item.rs:1137-1144](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/app-server-protocol/src/protocol/v2/item.rs#L1137-L1144)),
    `mcpToolCall` (`server`, `tool`, `arguments`, `result`, `error`),
    `dynamicToolCall` (`tool`, `arguments`, `contentItems`),
    `functionCallOutput`, `plan` (`text`), `subAgentActivity`,
    `webSearch` (`id`, `query`, `action`, `results`;
    [ext/items/src/web_search.rs:11-22](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/ext/items/src/web_search.rs#L11-L22)),
    `imageGeneration` (`revisedPrompt`, `status`, `savedPath`, and the
    image itself in `result`), `sleep` (`durationMs`), `hookPrompt`,
    `collabAgentToolCall`, `imageView`, `enteredReviewMode`,
    `exitedReviewMode`, `contextCompaction`.

  The two files join the rollout on the thread id, which is the rollout
  rows' `session_id`; the projection has no `cwd`, so its project path is
  taken from the `threads` row of the same thread. What it survives is
  what `state_5.sqlite` survives; it never holds a legacy rollout's
  thread.
- `logs_2.sqlite` `logs`: Codex's own tracing log, one row per log
  event of the app server and the TUI (`ts` and `ts_nanos` epoch seconds
  and nanoseconds, `level`, `target`, `feedback_log_body` the formatted
  message and fields, `thread_id`, `process_uuid`;
  [state/logs_migrations/0002_logs_feedback_log_body.sql:3-16](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/state/logs_migrations/0002_logs_feedback_log_body.sql#L3-L16),
  file name at
  [state/src/sqlite.rs:34](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/state/src/sqlite.rs#L34)).
  Every target is kept at trace level unless listed
  ([state/src/log_db.rs:61-63](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/state/src/log_db.rs#L61-L63)),
  and an event's `thread_id` field fills the `thread_id` column
  ([log_db.rs:572-579](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/state/src/log_db.rs#L572-L579)).
  Rows older than 10 days, or past a 64 MiB budget, are pruned
  ([state/src/runtime/logs_maintenance.rs:10-11](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/state/src/runtime/logs_maintenance.rs#L10-L11)),
  and Codex's thread delete removes a thread's rows
  ([state/src/runtime/threads.rs:1170-1173](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/state/src/runtime/threads.rs#L1170-L1173),
  called from
  [thread-store/src/local/delete_thread.rs:139-152](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/thread-store/src/local/delete_thread.rs#L139-L152)).
  The one row that marks an upload of a thread: a `/feedback` report
  sent to Sentry (an error-reporting service OpenAI uses for Codex
  feedback) logs `feedback event uploaded to Sentry` at `INFO` with the
  fields `thread_id` (the reported thread's id, or
  `no-active-thread-<uuid>` when none was open), `uploaded_attachments`
  (a count), `attachments_failed` (a boolean) and `elapsed_ms`
  ([feedback/src/lib.rs:749-755](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/feedback/src/lib.rs#L749-L755),
  [298-300](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/feedback/src/lib.rs#L298-L300)),
  under the target `codex_feedback` (the `codex-feedback` crate). It is
  written after the report event is accepted and its attachments are
  sent, whether or not the user agreed to upload logs, so
  `uploaded_attachments` is what tells the two apart. The TUI's
  `log/codex-tui.log` does not carry it: its default filter keeps only
  `codex_core`, `codex_tui`, `codex_rmcp_client` and
  `codex_realtime_webrtc`
  ([tui/src/startup_orchestration.rs:817-820](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/tui/src/startup_orchestration.rs#L817-L820)).
  The parser reads this row and the approval rows below, and no other
  row of the database
  ([section 8](#8-parser-plan-the-existing-parser)); a body field may
  come in any order, and the first logs migration named the body column
  `message`. Not seen on a real install: the feedback row is read from
  a synthetic fixture only.

  Codex Desktop writes the per-call permission decisions here and
  nowhere else (macOS, build 26.1013.40934, 2026-10-18;
  [section 1](#1-evidence)); `ts` was integer epoch seconds:
  - A user's decision in the approval dialog:
    `codex_app_server::outgoing_message` at `INFO`, `thread_id` empty,
    `<- response: CommandExecutionRequestApproval { request_id:
    Integer(<n>), response: CommandExecutionRequestApprovalResponse {
    decision: Decline } }` (or `Accept`), and in the same second
    `codex_core::session::handlers` at `DEBUG`, `thread_id` set,
    `Submission thread_id=<uuid> submission_id=<uuid>
    operation="exec_approval" ... op=ExecApproval { id: "exec-<uuid>",
    turn_id: Some("<uuid>"), decision: ... }`. A rejected call adds a
    `codex_core::tools::router` `ERROR` row. The `exec-<uuid>` id is
    the `id` of the governed `CommandExecution` or `FileChange` item
    (the rollout's `item_completed` line and the `thread_items` row),
    not the rollout's `call_id` (`call_<hex>`), so the join to the
    call is on the item id. The two rows word one decision differently:
    `denied` and `approved` on the handlers row, `Decline` and `Accept`
    on the response row. The response rows, read in the live database
    at 19:04Z, were no longer in the copy collected at 00:43Z (the
    `logs` table is pruned: it held 1,000 rows before sign-in and 2,944
    at collection, the oldest from 18:31:47Z), while both handlers rows
    were; the handlers row is the one that lasts.
  - An automatic decision in the Approve for me mode (auto-review):
    `codex_guardian_v2::async_scorer::approval` at `DEBUG`,
    `decide_request{approval_id="<uuid>"}: reviewing approval
    decision_source="synchronous_assessment" reason=Policy`, and rows
    inside the span `guardian_review{review_id="<uuid>"
    thread_id=<parent uuid> tool_call_id="exec-<uuid>"}`, whose
    `tool_call_id` is the governed item's id; the app-server events
    `item/autoApprovalReview/started`, `guardianWarning` and
    `item/autoApprovalReview/completed`. No
    `CommandExecutionRequestApproval` or `ExecApproval` row is written
    for it; the verdict itself is in the guardian thread's rollout.
  - A settings change: `operation="thread_settings"` with
    `op=ThreadSettings { requested_settings: ThreadSettingsOverrides {
    approval_policy: ..., approvals_reviewer: ..., sandbox_policy: ...,
    permission_profile: ... } }`, values seen `Some(OnRequest)`,
    `Some(Never)`, `Some(AutoReview)`, `Some(User)`,
    `Some("managed")`, `Some("disabled")` and `None`. The model is not
    in it; the rollout's `thread_settings_applied` is the model record.
  - Every app-server request by method (`thread/start`,
    `thread/resume`, `thread/fork`, `thread/delete`, `fs/remove`,
    `turn/start`, `command/exec`, `fs/readFile`, `gitDiffToRemote`,
    `remoteControl/*` and more), with `app_server.client_name` and
    `app_server.client_version` in its span: `Codex Desktop`
    `26.1013.40934`, `codex_chatgpt_ios_remote` `1.2026.279`,
    `codex_chatgpt_android_remote` `dev`. A paired phone can run a
    command on the host (`command/exec`) and read a file
    (`fs/readFile`) outside any turn; those requests are recorded only
    here.
- `state_5.sqlite` `remote_control_enrollments`: one row per remote
  control enrollment, the link that lets a ChatGPT client drive this
  host's app server (`codex remote-control`; `websocket_url`,
  `account_id`, `app_server_client_name`, `server_id`, `environment_id`,
  `server_name`, `updated_at`, and `remote_control_enabled` from
  migration 0037;
  [state/migrations/0024_remote_control_enrollments.sql:1-10](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/state/migrations/0024_remote_control_enrollments.sql#L1-L10),
  [0037_remote_control_enrollments_enabled.sql:1-2](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/state/migrations/0037_remote_control_enrollments_enabled.sql#L1-L2)).
  It names the host's enrollment, not a thread. Empty on the Windows
  install of [section 1](#1-evidence). On macOS (build 26.1013.40934,
  2026-10-18 and 2026-10-19) enabling remote control in the app
  (Settings > Connections > Control this Mac or PC) wrote one row:
  `websocket_url` the relay's websocket address on the chatgpt.com
  host (56 characters, no query string), `account_id`,
  `app_server_client_name` `Codex Desktop`, `server_id`
  (`srv_e_<hex>`), `environment_id` (`env_e_<hex>`), `server_name`
  the Mac's host name (`<name>.local`), `updated_at` and
  `remote_control_enabled` 1. Turning "Allow connections" off kept the
  row and set `remote_control_enabled` to 0 with a new `updated_at`;
  turning it on again reused the row, same ids, with 1. Revoking a
  paired phone and pairing a second phone changed nothing in it: the
  list of paired devices is held on the server. The row holds no
  token; the log says a server token is refreshed on re-enable, and
  where that token is stored was not found. The log rows (targets
  `codex_app_server_transport::transport::remote_control::enroll`,
  `::websocket` and `::client_tracker`, and the app-server requests):
  `remoteControl/enable`, `persisted remote control enrollment: ...`,
  `connected to app-server remote control websocket`, status changes
  between `Connecting`, `Connected` and `Disabled` (with
  `connection_end_reason=Disabled`), `remoteControl/disable`,
  `remoteControl/pairing/start`, `remoteControl/client/list` (polled
  while the Connections page is open), `remoteControl/client/revoke`
  (no device name in the row), the event
  `remoteControl/status/changed` when a phone connects, and
  `client_tracker` `... connection closed` when it leaves. The first
  pairing also wrote two top-level keys of `.codex-global-state.json`
  (below). **Parser reads** the row
  ([section 8](#8-parser-plan-the-existing-parser)).
- `sqlite/codex-dev.db`: written only by the ChatGPT desktop app (observed
  on Windows, ChatGPT 26.1007.9446.0, 2026-10-15; not in the Codex
  source this document cites). It is the app's own thread catalog and
  automation store. `local_thread_catalog` has one row per thread the
  app lists (`host_id`, `thread_id`, `display_title`,
  `source_created_at`, `source_updated_at`, `cwd`, `source_kind`,
  `source_detail`, `model_provider`, `git_branch`, `thread_source`,
  `project_id`, `conversation_origin`, `chatgpt_async_status` and
  bookkeeping columns): the local Codex threads as `source_kind`
  `vscode` with a `cwd`, and the ChatGPT chat as `source_kind` `chatgpt`
  with every other column but the title empty. After the later actions
  of [section 1](#1-evidence) it held five rows: three `vscode`, and two
  `chatgpt`, one with `conversation_origin` empty and one with
  `conversation_origin` `tpp` (what `tpp` denotes is not determined). `local_thread_catalog_hosts`
  (`host_id`, `host_kind`) held `local` and
  `chatgpt:<workspace uuid>:<user id>`. `automations` (`id`, `name`,
  `prompt`, `status`, `next_run_at`, `last_run_at`, `cwds`, `rrule`,
  `model`, `reasoning_effort`, `target_type`, `project_id`, `kind`,
  `target_thread_id`, `execution_environment`, `account_id`, `user_id`
  and more) and `automation_runs` (`thread_id`, `automation_id`,
  `status`, `thread_title`, `source_cwd`, `inbox_title`,
  `inbox_summary`, `archived_user_message`, `archived_assistant_message`
  and more) were empty after a first automation failed to save. The
  automation saved later held one `automations` row: `status` `ACTIVE`,
  `kind` `heartbeat`, `rrule` as in `automation.toml` below,
  `next_run_at` and `next_run_nominal_at` set (epoch ms), `last_run_at`
  null, `cwds` an empty JSON array, `target_thread_id` set,
  `auto_archive` 0 and every other column null (`model`,
  `reasoning_effort`, `target_type`, `project_id`,
  `execution_environment`, `local_environment_config_path`,
  `plugin_template_id`, `notification_policy`, `account_id`, `user_id`,
  `installation_id`, `legacy_automation_id`). `automation_runs` and
  `inbox_items` stayed empty, as the automation had not fired.
  Neither `conversation_origin` nor `chatgpt_async_status` appears in the
  Codex source (the app's code is not in the repository; see the `Sync:`
  paragraph of [section 8](#8-parser-plan-the-existing-parser)).
  `codex_schema_migrations` rows carry the app version (`app_version`
  `26.1007.71326`, `build_flavor` `prod`). The chat's text is not in it.
  The analyzer does not read it: the automation is read from
  `automation.toml`, and a run would be in `automation_runs`, which no
  real install has shown filled. On macOS (build 26.1013.40934,
  2026-10-18; [section 1](#1-evidence)) the database also had
  `local_thread_catalog_metadata`, `local_thread_catalog_scan_checkpoints`,
  `local_thread_catalog_scan_entries`, `local_thread_catalog_sync_state`
  (`host_id`, `watermark_updated_at`, `initial_build_complete`,
  `observation_sequence`, `last_full_reconciled_at`),
  `live_visualization_suggestions`, `local_app_server_feature_enablement`
  and a table not seen on Windows, `thread_timeline_ledger` (`host_id`,
  `thread_id`, `sequence`, `record_id`, `payload_json`), empty through
  every step. The `chatgpt` rows appeared at sign-in, before any chat,
  and were not updated when a conversation was continued in the app:
  they are the account's conversation list as of sign-in. Each
  Codex-mode thread added a `vscode` row with `thread_source` `user`
  and its `cwd`, `project_id` null even for the thread in a project,
  and the app's delete removed the deleted thread's row. The collector
  gathers the file through the `codex-cli|.codex` catalog line, under
  `codex-cli`.
- `automations/<slug>/automation.toml`: one directory per automation of
  the ChatGPT desktop app, named by a slug of the name the user typed
  (observed on Windows, 2026-10-15; not in the Codex source this
  document cites), beside `automations/.run-jitter-salt` (37 bytes,
  base64-class text). The file is flat TOML (383 bytes observed):
  `version` integer (1), `id` string (the slug), `kind` string
  (`heartbeat`), `name` string, `prompt` string (what the automation
  sends), `status` string (`ACTIVE`), `rrule` string (an iCalendar
  recurrence rule, the scheduling syntax of RFC 5545, of the form
  `RRULE:FREQ=WEEKLY;BYHOUR=9;BYMINUTE=0;BYDAY=MO,TU,WE,TH,FR`),
  `target_thread_id` string (the thread the automation runs in, whose
  rollout appeared when the automation was created), `created_at` and
  `updated_at` integers (epoch milliseconds). **Parser reads** (issue
  119). On macOS (build 26.1013.40934, 2026-10-18;
  [section 1](#1-evidence)) the file was 356 bytes with the same keys,
  `rrule`
  `RRULE:FREQ=WEEKLY;BYHOUR=19;BYMINUTE=45;BYDAY=SU,MO,TU,WE,TH,FR,SA`
  for a task the user set to run daily (the hour is local time), and
  `target_thread_id` the thread created with the task, into which both
  runs reported. Its `codex-dev.db` `automations` row had `status`
  `ACTIVE`, `kind` `heartbeat`, empty strings for `target_type`,
  `execution_environment`, `notification_policy`, `model` and
  `reasoning_effort`, `cwds` `[]`, `project_id` and
  `legacy_automation_id` null, `account_id`, `user_id` and
  `installation_id` set (null on Windows), `last_run_at` the last run,
  `next_run_nominal_at` the scheduled minute and `next_run_at` that
  minute moved by a jitter seeded from `.run-jitter-salt`. After a Run
  now and a scheduled run whose heartbeat decision was `DONT_NOTIFY`,
  `automation_runs` and `inbox_items` were still empty.
- `ambient-suggestions/<40 hex>/ambient-suggestions.json`: the desktop
  app's suggestions for a project (observed on Windows, 2026-10-15, 139
  bytes): `currentSuggestionIds` (empty list), `generatedAtMs` number,
  `projectRoot` absolute path, `suggestions` (empty list). Governed by
  `desktop.ambient-suggestions-enabled` in `config.toml`. Not read; a
  file holding suggestions has not been observed.

- `.codex-global-state.json` (and its `.bak`): the ChatGPT desktop
  app's state, one JSON object (macOS, build 26.1013.40934, 2026-10-18
  and 2026-10-19, [section 1](#1-evidence); not in the Codex source this
  document cites). The key `electron-persisted-atom-state` holds a JSON
  object, not a string, of the app's interface state; it and the top
  level name threads by id. The keys that record use of a thread:
  - `prompt-history`: a `global` list and one list per thread id, each
    entry `{markdown, document}` (the prompt as Markdown and as an
    editor document tree with `type` `doc`). It is the prompt history
    of Codex Desktop, which writes no `history.jsonl`.
  - `thread-descriptions-v1` (`{<thread id>: string}`),
    `thread-user-activity-times-v1` (keyed `["local","<thread id>"]`,
    a number, the last activity in epoch ms) and
    `client-thread-bindings-v1` (`client-new-thread:<uuid>` to a
    thread id).
  - `heartbeat-thread-permissions-by-id`: per thread id
    `activePermissionProfile` (`{id, extends}` or null),
    `approvalPolicy` (a string or the granular object),
    `approvalsReviewer`, `sandboxPolicy` (`type`, `writableRoots`,
    `networkAccess`, `excludeTmpdirEnvVar`, `excludeSlashTmp`): each
    thread's standing permission state, in camelCase
    (`workspaceWrite` here, `workspace-write` in the rollout). A
    one-off approval leaves it unchanged, and Full access was never
    stored in it.
  - `agent-mode-by-host-id` (`{local: "guardian-approvals"}`),
    `permission-selection-by-host-id:local` (`{kind: "agent-mode",
    agentMode}`) and `preferred-non-full-access-agent-mode-by-host-id`:
    the permission mode the app starts threads in (the scheduled task's
    new thread started in auto-review). Only `guardian-approvals` was
    observed.
  - `composer-recent-model-configurations-v1`
    (`[{model, reasoningEffort, serviceTier}]`, most recent first) and
    `composer-model-picker-selection-mode-v1`.
  - `codex-writing-block-deleted-thread-v1:<thread id>`, `true`:
    written when the thread is deleted in the app, absent for a live
    thread.
  - Top level: `projectless-thread-ids` (a list of thread ids),
    `thread-projectless-output-directories` and
    `thread-workspace-root-hints` (`{<thread id>: path}`), and, from
    the first remote-control pairing,
    `electron-local-remote-control-environment-id` (a string) and
    `codex-mobile-has-connected-device` (a boolean).
  - Projects and files: `local-projects`
    (`{<uuid>: {createdAt, id, name, rootPaths, updatedAt}}`),
    `thread-project-assignments`, `recent-workspace-files-v3` (the
    files a thread wrote, keyed
    `["local","client-new-thread:<uuid>","<path>"]`) and
    `composer-prompt-drafts-v2` (an unsent draft per composer surface).
  - `external-agent-import-discovery:claude-code`, `:claude-cowork`
    and `:cursor` (`detectedAtMs`, `requestKey`, `result` with `items`
    and `unsupportedProjects`), written at sign-in: the app looks for
    other agents' state.

  The ChatGPT account id appears inside key names:
  `chatgpt-work-models-v1/user-<account id>/<uuid>` and the keys of
  `new-task-execution-by-account-project` (`{kind: "cloud"}`). The
  app's delete removed `thread-client-id-v1:local%3A<thread id>` and
  kept every other key naming the thread, so the file outlives a
  deleted thread with its prompts. The collector flags the file
  `secret: true` and collects it by default. **Parser reads**, as a
  secondary source ([section 8](#8-parser-plan-the-existing-parser)).
- `thread-writer-locks/` (`.coordination.lock` and one
  `<thread id>.lock` per open thread, 0 bytes) and
  `shell_snapshots/<thread id>.<unix ns>.sh` (macOS, build
  26.1013.40934, 2026-10-18): working files of the running app. The
  locks of closed threads went at the next launch. A prewarmed reviewer
  (a guardian session the app warms up in advance, observed at a
  resume and at a scheduled task's creation) left a lock for a thread
  id with no rollout, `threads` row or index line, so a lock is not a
  session. A shell snapshot (2,135 to 2,299 bytes, 43 lines: a
  `# Snapshot file` header, 29 `export` lines, 2 aliases,
  `unalias -a`, `setopt` lines) replays the user's exported shell
  environment for the sandbox, one per thread per resume or turn with
  the older ones deleted. The exported names include
  `BROWSER_USE_ACCESS_VERIFYING_IDENTITY`,
  `CODEX_TASK_WORKSPACE_VERIFYING_IDENTITY`,
  `CODEX_APP_TOOLS_PIPE_PATH`, `SSH_AUTH_SOCK`, `HOME`, `USER` and
  `TMPDIR`, so an API key the user exports in the login shell is
  copied here; collector 1.15.0 flags the files `secret: true`
  ([section 3 of `collectors/research/codex-cli.md`](../../collectors/research/codex-cli.md#3-credentials)).
  The parser reads neither.

Opened only from scratchpad copies, and only for table names, row counts
and key names.

## 6. Timestamps, ids, project, branch, model, subagents

- **Timestamps.** Line `timestamp` and `session_meta.payload.timestamp`:
  UTC `YYYY-MM-DDThh:mm:ss.mmmZ`, the line one taken at write time
  ([recorder.rs:927-933](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/rollout/src/recorder.rs#L927-L933), [2077-2082](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/rollout/src/recorder.rs#L2077-L2082)); local values all had three fraction
  digits and `Z`. `task_*` `started_at`/`completed_at`: epoch seconds;
  `item_completed` `*_at_ms`: epoch ms; `create_time`: fractional epoch
  seconds; `history.jsonl` `ts`: epoch seconds.
- **Ids.** `session_meta.payload.id` is the thread id and the file-name
  UUID; `session_id` is the root thread's id, so a subagent's rollout has
  `id` ≠ `session_id`. Reverted rollouts end `<thread id>_<rollout id>`.
- **Surface.** `session_meta.payload.originator` is the key that tells
  the surfaces apart: `codex-tui` for the CLI and `Codex Desktop` for
  the ChatGPT desktop app. `source` was `vscode` for both on the Windows
  install observed on 2026-10-15 (desktop 0.162.0-alpha.17.2, standalone
  CLI 0.162.1), so it does not separate them.
- **Account and user.** `session_meta.payload.creator_account_id` (a
  UUID) and `creator_user_id` (the ChatGPT user id, 29 characters) name
  who created the thread; Codex Desktop fills them (observed on Windows,
  2026-10-15). The same pair is in the `state_5.sqlite` `threads`
  columns of the same names, and the user id, with the ChatGPT workspace
  id, in the `codex-dev.db` `local_thread_catalog_hosts` host id
  `chatgpt:<workspace uuid>:<user id>` ([section 5](#5-other-files)).
- **Project.** `session_meta.payload.cwd`, updated per turn by
  `turn_context.payload.cwd`; `workspace_roots` lists extra roots.
- **Branch.** `session_meta.payload.git.branch`, set once at thread
  creation, absent outside a git repository.
- **Model.** `turn_context.payload.model`; `model_provider` on
  `session_meta`. No per-message model. Codex Desktop also appends
  `event_msg` `thread_settings_applied` (`model`, `reasoning_effort`
  and the permission fields) the moment the user changes a setting,
  before the next turn (macOS, build 26.1013.40934, 2026-10-18;
  [section 1](#1-evidence)); `state_5.sqlite` `threads.model` keeps
  only the latest.
- **Subagents.** Each spawned agent has its own rollout whose
  `session_meta` has `parent_thread_id`, `agent_nickname`, `agent_role`,
  `agent_path`, `thread_source: "subagent"` and `source:
  {"subagent": {"thread_spawn": {parent_thread_id, depth, ...}}}`;
  messages between agents are `inter_agent_communication` lines.
  Codex Desktop's guardian reviewer has `parent_thread_id`,
  `thread_source` `guardian_review` and `source`
  `{"subagent": {"other": "guardian"}}`, no `thread_spawn` and no
  `thread_spawn_edges` row (macOS, 2026-10-18).
- **Forks.** `forked_from_id` on the child. A copied fork re-appends the
  parent's records into the child file at fork time, so they carry the
  fork's line timestamps; a referenced (paginated) fork keeps them in the
  parent file behind `history_base` (`thread_id`, `end_ordinal_exclusive`,
  `end_byte_offset`)
  ([core/src/session/mod.rs:1672-1695](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/core/src/session/mod.rs#L1672-L1695),
  [protocol.rs:3101-3115](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/protocol.rs#L3101-L3115)).
  Codex's own metadata sync only trusts a `session_meta` whose `id` is the
  file's thread, which implies copied files can hold an ancestor's
  `session_meta` too
  ([thread-store/src/thread_metadata_sync.rs:246-256](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/thread-store/src/thread_metadata_sync.rs#L246-L256)).

## 7. Variants and drift

- **History mode.** `session_meta.history_mode` (`legacy` default,
  `paginated`; [protocol.rs:775-782](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/protocol.rs#L775-L782)). The app server starts
  non-ephemeral threads paginated when the store supports it
  ([app-server/src/request_processors/thread_processor.rs:1462-1465](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/app-server/src/request_processors/thread_processor.rs#L1462-L1465)); the local TUI
  thread was paginated. Paginated files add `ordinal` and `item_completed`
  items and drop the legacy `user_message`/`agent_message` events. A
  background legacy-to-paginated rewrite exists behind
  `background_paginated_rollout_migration`, off by default
  ([features/src/lib.rs:1224-1229](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/features/src/lib.rs#L1224-L1229),
  [thread-store/src/local/rollout_migration.rs:1-9](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/thread-store/src/local/rollout_migration.rs#L1-L9)).
- **Compression and archive.** `.jsonl.zst` and `archived_sessions/`
  ([section 2](#2-transcript-files)); Codex materialises a compressed file back to `.jsonl` before
  appending to it
  ([compression.rs:104-105](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/rollout/src/compression.rs#L104-L105)), so either form may be present.
- **Flat layout.** Older releases wrote `sessions/rollout-<time>-<uuid>.jsonl`
  without date directories (the example in
  [recorder.rs:82](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/rollout/src/recorder.rs#L82)); the current lister walks only
  `YYYY/MM/DD`
  ([list.rs:900-920](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/rollout/src/list.rs#L900-L920)).
- **Standalone CLI and desktop app on one host.** On Windows the
  standalone CLI (installed by OpenAI's PowerShell installer under
  `.codex/packages/standalone`) and Codex Desktop inside the ChatGPT app
  write the same `.codex` tree, sessions and login (observed
  2026-10-15, CLI 0.162.1, desktop 0.162.0-alpha.17.2). Their rollouts
  have the same envelope and `session_meta` keys and differ in
  `originator` and `cli_version` ([section 6](#6-timestamps-ids-project-branch-model-subagents));
  only the CLI wrote `history.jsonl`. The parser reads both alike.
- **Renames kept for compatibility.** `session_meta` without `session_id`,
  `agent_type` for `agent_role`, `turn_started`/`turn_complete` aliases,
  `compaction_summary` for `compaction`; `TurnContextItem.summary` is
  written only for older readers.
- **Not determined at this commit:** whether pre-envelope rollouts (no
  `type`/`payload` wrapper) exist on disk from very early releases; the
  current reader rejects lines without `timestamp`.

## 8. Parser plan (the existing parser)

`CodexParser` wants
`^\.codex/(?:archived_)?sessions/(?:.*/)?rollout-[^/]*\.jsonl(?:\.zst)?$`
and `.codex/history.jsonl`. Until `session_meta` is read, the session id is
the thread id in the file name: the last UUID, or the first of a reverted
rollout's `<thread id>_<rollout id>`. The parser reads the whole file before
emitting rows, so that an `item_completed` line can be checked against every
`response_item` id and `call_id` in the file.

| Column | Source |
| --- | --- |
| timestamp_utc | line `timestamp`; `session_meta.payload.timestamp` for the start, subagent and fork rows; `item_completed` `started_at_ms` / `completed_at_ms` for the rows built from a turn item; history `ts` (s) |
| session_id | the file's first `session_meta.payload.id`, else its `session_id`, else the file-name thread id; a later `session_meta` never changes it; history `session_id` |
| project_path | first `session_meta.payload.cwd`, replaced by each `turn_context.payload.cwd` |
| git_branch | first `session_meta.payload.git.branch` |
| model | `turn_context.payload.model` (empty before the first `turn_context`) |
| turn_type | coverage table below |
| tool_name | `name`; `shell` for `local_shell_call` and `CommandExecution`, `web_search` for `web_search_call` and web-search turn items, `tool_search`, `<server>.<tool>` for `McpToolCall`, `apply_patch` for `FileChange` |
| tool_use_id | `call_id` (call falls back to `id`); a turn item's `id` |
| text | message: `content[].text` joined, prefixed `<role>: ` for developer; user-role context `context: <kind>: <text>`; tool_use: `arguments` or `input`, `action.command` joined, `action.query`, `arguments` JSON; tool_result: `output` string or `[].text` joined, prefixed `[exit N]` when the matching `CommandExecution` item has a non-zero `exit_code`; thinking: `summary[].text`, else `content[].text` |

| Record | Row |
| --- | --- |
| first `session_meta` | `system` ("session start: originator version provider cwd", then ` account=<creator_account_id> user=<creator_user_id>` with only the keys present, issue 118); plus `system` `subagent <id> of <parent> [agent_path= agent_role= agent_nickname=]` when `parent_thread_id`, `source.subagent.thread_spawn.parent_thread_id`, or a `session_id` other than `id` on a non-fork names a parent; plus `system` `forked from <id>` for `forked_from_id` |
| later `session_meta` | `system` `copied from ancestor: session start ... id= cwd=` when its id differs; none when it repeats the file's own |
| `turn_context` | sets project and model; `system` `model: <model>` at the first one that names a model and `model: <old> -> <new>` at each later one whose `model` differs; `system` `permission mode: approval=<approval_policy> sandbox=<sandbox_policy> profile=<permission_profile> network=<network> reviewer=<approvals_reviewer> profile_id=<active_permission_profile.id>` at the first one with any of the fields and `permission mode: <old> -> <new>` on every change to the composite (a missing field is `-`, an object compact JSON); both at the line's `timestamp`, before the turn's rows, keyed per session |
| `event_msg` `thread_settings_applied` (Codex Desktop) | the same `model:` and `permission mode:` tracking as `turn_context`, at the event's `timestamp`, so a change the user makes between turns (a model switch, Approve for me, Full access and its revert) is dated when it was made rather than at the next turn. The event is the thread's settings, not a turn's: it carries `model`, `approval_policy`, `approvals_reviewer` and `active_permission_profile`, no `sandbox_policy`, and a `permission_profile` without the roots a turn adds, so only the three thread-level fields come from it; `sandbox` and `profile` stay as the last `turn_context` had them, or read `-` once the access level changed until the next `turn_context`, and an event before the thread's first `turn_context` is folded into that turn's row (issue 160) |
| `response_item` with `metadata.inherited_user_message` | none (copied from the parent thread) |
| `response_item` `message` user | per `content_item_kinds` run: `user` for `user.*`, `unknown` or empty kinds; `system` `context: <kind>: ...` for any other kind; without a kinds list as long as `content`, per block: `system` `context: <marker name>: ...` for a block that is wholly one of the harness wrappers below, else `user`. In a subagent file the first prompt is `system` `subagent task: ...`; later ones stay `user` (below) |
| `response_item` `message` assistant / developer | `assistant` / `system` (`developer: ...`); empty text skipped |
| `response_item` `function_call`, `custom_tool_call`, `local_shell_call`, `web_search_call`, `tool_search_call` | `tool_use` |
| `response_item` `function_call_output`, `custom_tool_call_output`, `local_shell_call_output`, `tool_search_output` (tool names) | `tool_result` |
| `response_item` `agent_message`, `inter_agent_communication` | `system` `agent message <author> -> <recipients>: ...` (`subagent task:` for a subagent's first prompt); an `inter_agent_communication` whose `id` a response item carries is skipped |
| `response_item` `image_generation_call` | `system` `image generation: <revised_prompt> status=...` |
| `response_item` `reasoning` | `thinking` with `--include-thinking` when it has text, else skipped |
| `response_item` `additional_tools`, `compaction`, `context_compaction`, `configuration_update` | skipped (no readable content) |
| `event_msg` `task_started`, `task_complete` | `system`; `task_started turn=<id>` as before (so the `thread_history_1.sqlite` copy still pairs with it), followed by `turn trigger: <turn_trigger> turn=<id>` when `turn_attribution.turn_trigger` is set (values seen in [section 1](#1-evidence): `composer`, `remote_ios`, `remote_android`, `guardian_review`, `scheduled_task_setup`, `automation_heartbeat_run_now`, `automation_heartbeat_scheduled`; a `remote_*` turn came from a paired phone) |
| `event_msg` `task_complete` of a guardian review thread (`thread_source` `guardian_review`) | `system` `permission decision: <outcome> (auto_review risk_level=<risk_level> user_authorization=<user_authorization>) ...` from the JSON verdict in `last_agent_message`, naming the reviewer thread and carrying the `rationale` in full, at the line's `timestamp`, with `session_id` the governed thread (`session_meta.parent_thread_id`) |
| `event_msg` `turn_aborted` | `system` `turn aborted: <reason> [error message]` |
| `event_msg` `thread_rolled_back` | `system` `rolled back <n> turns`; earlier rows are not changed |
| `event_msg` `item_completed` `UserMessage`, `AgentMessage`, `Reasoning`, `HookPrompt`, `ContextCompaction` | skipped (repeat a response item or `compacted`) |
| `event_msg` `item_completed`, other items whose `id` a response item carries as `id` or `call_id` | skipped; a `CommandExecution` exit code still marks the call's `tool_result` |
| `event_msg` `item_completed` `CommandExecution`, `McpToolCall`, `DynamicToolCall`, `FileChange`, `WebSearch`, `Extension` `web.search` not carried | `tool_use` + `tool_result` on the item `id` |
| `event_msg` `item_completed` `FunctionCallOutput` not carried | `tool_result` |
| `event_msg` `item_completed` `Plan`, `SubAgentActivity`, image generation, `clock.sleep`, others not carried | `system` (`plan: ...`, `subagent activity: ...`, `image generation: ...`, `sleep: N ms`, `item <type>: <JSON>`) |
| `event_msg` legacy `user_message`, `agent_message`, `agent_reasoning`, and the rest | skipped |
| `compacted` | `system` `compaction summary: <message>`, or `compaction: replacement history of N items` |
| `realtime_item` `transcript_segment` | `user` or `assistant` by `role` |
| `realtime_item` other types | `system` `realtime: <type> <JSON>` |
| `token_usage_record`, `world_state`, `inter_agent_communication_metadata`, `retained_context`, `security_risk_score` | skipped |
| bad line, in a rollout or in `history.jsonl` | one `system` row per bad line at the end of the file's rows, `parser: unparseable line (<decoder reason>): <the line in full>`, `source_line` the bad line, `session_id` the rollout's session (empty for `history.jsonl`) |
| cut or corrupt zstd frame | one `system` row `parser: zstd: <message>` at the end, `source_line` the line after the last one decoded |
| `history.jsonl` line | `user` |
| `state_5.sqlite` `threads` row (secondary) | `system` `thread record: <id> title=<title> rollout=<rollout_path>`, then ` name=`, ` branch=`, ` model=` (the last turn's) and ` archived` when set, at `created_at_ms` (else `created_at`); then `first_user_message` as `user` with no timestamp, `system` `subagent task: ...` in a subagent's thread |
| `thread_history_1.sqlite` `thread_turns` row (secondary) | `system` `task_started turn=<id>` at `started_at`; `task_complete turn=<id> duration_ms=<n>` at `completed_at` for a completed or failed turn; an interrupted turn has no closing row (its reason is only in the rollout) |
| `thread_history_1.sqlite` `thread_items` row (secondary) | `userMessage` `user`, `agentMessage` `assistant`, `reasoning` `thinking` (opt-in), at `completed_at_ms`; `hookPrompt`, `contextCompaction` none; any other item renamed to the turn-item form and rendered as the `item_completed` rows above, at `started_at_ms` and `completed_at_ms` (else `created_at_ms`); a bad `item_json` is counted in one `system` row |
| `automations/<slug>/automation.toml` (Codex only) | one `system` row `scheduled task: <id> name=<name> kind=<kind> status=<status> rrule=<rrule> target_thread=<target_thread_id> created=<created_at> updated=<updated_at> (from <file>, file mtime) prompt: <prompt>` at the file's modification time, `session_id` the target thread; an unreadable file is one `system` row (issue 119) |
| `logs_2.sqlite` `logs` row `codex_core::session::handlers` `op=ExecApproval` or `codex_app_server::outgoing_message` `CommandExecutionRequestApproval` (Codex Desktop) | `system` `permission decision: <decision> exec <item id> turn=<turn id> (from logs_<N>.sqlite logs, ts)` at `ts` from the handlers row (`denied`, `approved` seen), `session_id` the row's thread id, `tool_use_id` the governed item's id (`exec-<uuid>`, [section 5](#5-other-files)); a response row (`Decline`, `Accept`) with no handlers row within two seconds is `permission decision: <decision> request <n> (from logs_<N>.sqlite logs, ts)` with no session (issue 160) |
| `state_5.sqlite` `remote_control_enrollments` row | `system` `remote control: enabled=<0\|1> server=<server_id> environment=<environment_id> host=<server_name> client=<app_server_client_name> account=<account_id>` at `updated_at`, `session_id` empty (issue 160) |
| `.codex-global-state.json` (secondary, Codex Desktop) | `user` for each `prompt-history` entry of a thread, with an empty `timestamp_utc` (matched on text and session), `session_id` the thread id; `system` `session deleted: <id>` for each `codex-writing-block-deleted-thread-v1:<id>` key and `system` `permission mode (standing): ...` for each `heartbeat-thread-permissions-by-id` entry, at the file's modification time; `system` `thread description: ...` for each `thread-descriptions-v1` entry; one `system` `remote control: mobile device connected=<bool> environment=<id>` row from the two top-level keys; a file that does not decode is one `parser:` row (issue 160) |

Sources, by role (issue 122). The rollouts are the primary store: Codex
writes every other file from them. `history.jsonl`, `state_5.sqlite`,
`thread_history_1.sqlite` and Codex Desktop's `.codex-global-state.json`
are secondary sources, read on every run; the
timeline drops a row of theirs that a rollout row of the same session
repeats (same `turn_type` and `text`, time within 2 seconds, or any time
for a row with none) and keeps the rest. How each joins:

| Source | session_id | project_path | Time |
| --- | --- | --- | --- |
| `history.jsonl` | `session_id` | none | `ts`, whole seconds |
| `state_5.sqlite` thread record | `threads.id` | `threads.cwd` | `created_at_ms`, the thread's creation |
| `state_5.sqlite` first prompt | `threads.id` | `threads.cwd` | none: matches on text and session |
| `thread_history_1.sqlite` | `thread_id` | the same thread's `threads.cwd` from the `state_5.sqlite` beside it, else empty | the item's or turn's own, as the rollout row it repeats |
| `.codex-global-state.json` prompt history | the thread id in the key | none | none: matches on text and session |

The projection's rows take the times of the rollout rows they repeat:
a message at `completed_at_ms`, when the response item is written; a
tool item at its start and end, as the rollout reader stamps an
`item_completed` item; a turn at its `started_at` and `completed_at`,
under a second from the `task_started` and `task_complete` lines. The
fixture pairs all of them within the default 2 seconds. A tool call
made through a function call has a rollout `tool_use` text of the
model's arguments (`{"cmd": ...}` for `exec_command`, the patch for
`apply_patch`) and a projection text of the parsed command or the
changed paths, so the two never pair on text; `dedup.deduplicate` pairs
`tool_use` and `tool_result` rows that both carry a `tool_use_id` on
that id instead (analyzer 0.13.0). Known misses, each shown twice: a web
search longer than 2 seconds whose rollout also holds the
`web_search_call` response item, stamped at the end; on Open
Interpreter, an `agentMessage`, stamped at its start because the fork
has no migration 0007. A thread's first prompt is in three secondary
sources (`history.jsonl`, `first_user_message`, the projection's
`userMessage`); one pairs with the rollout's prompt, and
`dedup.deduplicate` collapses the other two onto that copy, the undated
`first_user_message` included, so only the rollout's row is kept
(fixture: `FIXTURE_DEDUPLICATED` in `tests/test_cli.py`).

Permission state is the per-turn `turn_context` policy above and, on
Codex Desktop, every `thread_settings_applied` event and the standing
per-thread entries of `.codex-global-state.json`. The rollout holds no
per-call decision: approval requests and their answers are transient
events that the rollout never stores
([policy.rs:160-223](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/rollout/src/policy.rs#L160-L223)), so a
rollout shows what the policy allowed, not what the user approved. Codex
Desktop logs the user's answers in `logs_2.sqlite` and records an
automatic answer as the verdict of a guardian review thread (macOS,
build 26.1013.40934, 2026-10-18; [section 5](#5-other-files)); the
parser yields a `permission decision:` row from each, joined to the
governed call on its item id. The approval dialog of that build
offered no standing "always allow" grant for a command. The model is
recorded per turn, in `turn_context.model`, and on Codex Desktop also
at each change, in `thread_settings_applied`; there is no per-message
model, so the model rows follow the turns and the settings events.

Sync: Codex has no session sync. The thread store is local only: the
two backends are `Local` (rollouts and SQLite) and `InMemory`
([core/src/config/mod.rs:599-607](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/core/src/config/mod.rs#L599-L607)),
and the old `experimental_thread_store_endpoint` for a remote store is
now refused at load
([3251-3254](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/core/src/config/mod.rs#L3251-L3254)).
The thread metadata sync of [section 6](#6-timestamps-ids-project-branch-model-subagents)
copies rollout facts into `state_5.sqlite` and calls no server
([thread-store/src/thread_metadata_sync.rs:34-38](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/thread-store/src/thread_metadata_sync.rs#L34-L38)).
`codex resume` reopens a local rollout
([cli/src/main.rs:206-207](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/cli/src/main.rs#L206-L207)), and the
app server's `thread/*` methods have no share or upload method. What
does leave the host, beyond the model API call:

- **`/feedback`** ("send logs to maintainers";
  [tui/src/slash_command.rs:73](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/tui/src/slash_command.rs#L73),
  [93](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/tui/src/slash_command.rs#L93)) sends a report to OpenAI's
  Sentry project
  ([feedback/src/lib.rs:60-61](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/feedback/src/lib.rs#L60-L61)). The
  TUI asks "Upload logs?" and lists the files
  ([tui/src/bottom_pane/feedback_view.rs:252](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/tui/src/bottom_pane/feedback_view.rs#L252),
  [282-285](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/tui/src/bottom_pane/feedback_view.rs#L282-L285)); on yes
  the open thread's rollout
  ([tui/src/app/background_requests.rs:623-627](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/tui/src/app/background_requests.rs#L623-L627))
  and the rollouts of its subagent threads are attached
  ([app-server/src/request_processors/feedback_processor.rs:179-196](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/app-server/src/request_processors/feedback_processor.rs#L179-L196)),
  packed into `rollouts.tar.gz` in a system temporary directory
  ([feedback/src/lib.rs:840-853](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/feedback/src/lib.rs#L840-L853)).
  On no, the report carries the category, the note and tags only, and
  the TUI says "Feedback recorded (no logs)"
  ([feedback_view.rs:54-58](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/tui/src/bottom_pane/feedback_view.rs#L54-L58)).
  Opt-in per report; the whole flow is on by default and turned off by
  `[feedback] enabled = false` in `config.toml`
  ([config/src/types.rs:233-236](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/config/src/types.rs#L233-L236),
  [core/src/config/mod.rs:4498-4502](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/core/src/config/mod.rs#L4498-L4502),
  [feedback_processor.rs:62-66](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/app-server/src/request_processors/feedback_processor.rs#L62-L66)).
  The marker is the `logs_2.sqlite` row of [section 5](#5-other-files).
  The parser yields one `system` row per such log row (`target`
  `codex_feedback` and the message `feedback event uploaded to Sentry`;
  the other `codex_feedback` rows report attachment failures and are not
  uploads), `session synced: feedback report uploaded to Sentry,
  attachments <uploaded_attachments> failed <attachments_failed> (from
  logs_2.sqlite logs, ts)`, `-` for a field the body lacks, at `ts` plus
  `ts_nanos`, with `session_id` the body's `thread_id` (empty for a
  `no-active-thread-` id) and the project and branch of that thread's
  `threads` row; the parser sets `records_sync`, so a thread without the
  row is `synced` `no` in `sessions.jsonl`. A report with 0 attachments
  sent no rollout. Fixture only: no real install has shown the row. The row survives the rollout's
  loss outside Codex for up to 10 days; Codex's own thread delete
  removes it with the thread, Codex offers no delete of the Sentry
  copy, and nothing local records one.
- **`codex cloud`** (experimental;
  [cli/src/main.rs:227-229](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/cli/src/main.rs#L227-L229)) creates a
  Codex Cloud task, a run on OpenAI's servers against a GitHub branch:
  the typed prompt, the environment id and the branch, plus a local
  diff only when `CODEX_STARTING_DIFF` is set
  ([cloud-tasks-client/src/http.rs:332-372](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/cloud-tasks-client/src/http.rs#L332-L372)).
  It sends no local thread; the task's transcript is server-side, and
  `codex apply` fetches a task's diff back
  ([chatgpt/src/get_task.rs:37-38](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/chatgpt/src/get_task.rs#L37-L38)).
  Its only local trace is an `error.log` that it appends to in the
  directory it was started from, not under `~/.codex`
  ([cloud-tasks/src/util.rs:18-28](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/cloud-tasks/src/util.rs#L18-L28),
  [cloud-tasks-client/src/http.rs:911-920](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/cloud-tasks-client/src/http.rs#L911-L920)),
  with lines `[<RFC 3339 time>] new_task: created id=<task id> env=<env
  id> prompt_chars=<n>`
  ([http.rs:374-381](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/cloud-tasks-client/src/http.rs#L374-L381)),
  the GitHub origins it matched
  ([cloud-tasks/src/env_detect.rs:51](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/cloud-tasks/src/env_detect.rs#L51))
  and the `account_id` it authenticated as
  ([cloud-tasks/src/lib.rs:103](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/cloud-tasks/src/lib.rs#L103)). No
  catalog line collects that file; no row is proposed until it is.
- **`codex remote-control`** (experimental;
  [cli/src/main.rs:176-177](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/cli/src/main.rs#L176-L177),
  [cli/src/remote_control_cmd.rs:53-62](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/cli/src/remote_control_cmd.rs#L53-L62))
  enrolls the host's app server with the ChatGPT backend
  (`wham/remote/control/environments`;
  [app-server-transport/src/transport/remote_control/clients.rs:268-270](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/app-server-transport/src/transport/remote_control/clients.rs#L268-L270))
  so a ChatGPT client can drive it over a websocket. Threads stay in
  the local store and the remote client reads them live through the
  app server. Observed with the ChatGPT app's remote connections
  (Settings > Connections > Control this Mac or PC; build
  26.1013.40934, 2026-10-18 and 2026-10-19, [section 1](#1-evidence)),
  it leaves two records: the host-level `remote_control_enrollments`
  row of [section 5](#5-other-files), which the parser yields as a
  `remote control:` row, and a per-turn mark, `turn_attribution.turn_trigger`
  `remote_ios` or `remote_android` on a turn sent from a paired phone,
  which the parser's `turn trigger:` row carries; the
  phone's own connection is in `logs_2.sqlite`. The vendor page
  [Remote connections | ChatGPT Learn](https://learn.chatgpt.com/docs/remote-connections)
  (read 2026-10-18) says "Repository files and local documents come
  from the connected host". The relay carries control, not a copy of
  the thread, so the parser marks no session synced or relayed for it.
- **`--remote <ADDR>`** points the TUI at an app server the user
  runs elsewhere
  ([cli/src/main.rs:962-974](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/cli/src/main.rs#L962-L974)). The
  rollout is written on that server's host, but the TUI still appends
  each prompt to the local `history.jsonl`
  ([tui/src/app/thread_routing.rs:557-566](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/tui/src/app/thread_routing.rs#L557-L566)),
  so a `history.jsonl` session with no local rollout may be such a
  thread. Not a vendor upload.
- **Analytics** go to `<chatgpt base URL>/codex/analytics-events/events`
  ([analytics/src/client.rs:154](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/analytics/src/client.rs#L154)) as
  events keyed by thread id
  ([analytics/src/events.rs:257](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/analytics/src/events.rs#L257));
  no prompt or reply text field was found (searched `prompt`, `text`,
  `user_message` in `analytics/src`). Turned off by `[analytics]
  enabled = false`
  ([config/src/types.rs:223-228](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/config/src/types.rs#L223-L228)).
  OpenTelemetry export, which can carry prompts and replies, is off by
  default and goes only to an exporter the user configures
  ([config/src/types.rs:597-611](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/config/src/types.rs#L597-L611),
  [647-657](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/config/src/types.rs#L647-L657)). Image attachments are
  kept inline in the rollout; the one attachment store uploads nothing
  ([attachment-store/src/lib.rs:160-170](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/attachment-store/src/lib.rs#L160-L170)).

The ChatGPT desktop app's own sync state is outside this source: its
client code is not in the repository (searched
`chatgpt-conversation-resume-tokens`, `resume-tokens`,
`conversation_origin`, `chatgpt_async_status`, `codex-dev.db`,
`local_thread_catalog` and `electron-persisted-atom-state` across the
clone; the only matches are unrelated token-usage replay code). The
`chatgpt` rows of `codex-dev.db` `local_thread_catalog` and the
resume tokens in `.codex-global-state.json` (collector document,
[section 3](../../collectors/research/codex-cli.md#3-credentials)) are
the app's index of ChatGPT conversations that live on the server; what
`chatgpt_async_status` and `conversation_origin` `tpp` mean, and
whether a local Codex thread is ever uploaded as a ChatGPT
conversation, was not determined from source. The macOS round of
2026-10-18 ([section 1](#1-evidence), build 26.1013.40934) answered the
second question for that build. The `chatgpt` catalog rows are written
at sign-in from the account's conversation list and were not refreshed
when the user continued one of those conversations in the app; the
reply left no transcript locally and never passed through the app
server. The app's Codex-mode threads did not appear in the Codex area
of chatgpt.com (a user report). So the account's conversation list is
copied one way, account to app, as a sign-in snapshot, and Codex-mode
threads are not uploaded. The vendor page
[Codex Cloud](https://learn.chatgpt.com/docs/cloud) (read 2026-10-18)
describes server-side tasks, where "Each task has its own workspace and
can keep working while your computer is asleep", and says nothing about
uploading local threads. No `chatgpt-conversation-resume-tokens` key had
appeared in the global state by the end of sign-in. A delete in the app
removes the rollout, the index line and the database rows, and the
global state keeps the prompts and a deletion marker
([section 5](#5-other-files)); with no remote copy, the delete dialog
offered none to remove. What `chatgpt_async_status` and
`conversation_origin` `tpp` mean is still not determined.

Rollouts without content kinds are classified per content block by the
wrappers Codex itself recognises as injected user-role context
([core/src/context/contextual_user_message.rs:22-37](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/core/src/context/contextual_user_message.rs#L22-L37)).
As in Codex's own check, the block must begin with the open marker after
leading whitespace and end with the close marker, ignoring ASCII case
([context-fragments/src/fragment.rs:116-130](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/context-fragments/src/fragment.rs#L116-L130)), so a tag a person types inside a prompt leaves it `user`:

| Marker name | Open … close | Source |
| --- | --- | --- |
| `agents_md_instructions` | `# AGENTS.md instructions` … `</INSTRUCTIONS>` | [core/src/context/user_instructions.rs:23-25](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/core/src/context/user_instructions.rs#L23-L25) |
| `environment_context` | `<environment_context>` … `</environment_context>` | [protocol/src/protocol.rs:120-121](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/protocol.rs#L120-L121), [core/src/context/world_state/environment.rs:524-529](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/core/src/context/world_state/environment.rs#L524-L529) |
| `agent_message_board_notification` | `<agent_message_board_notification>` … closing tag | [core/src/context/agent_message_board_notification.rs:19-25](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/core/src/context/agent_message_board_notification.rs#L19-L25) |
| `skill` | `<skill>` … `</skill>` | [ext/skills/src/fragments.rs:89-91](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/ext/skills/src/fragments.rs#L89-L91) |
| `user_shell_command` | `<user_shell_command>` … closing tag | [core/src/context/user_shell_command.rs:44](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/core/src/context/user_shell_command.rs#L44) |
| `turn_aborted` | `<turn_aborted>` … closing tag | [core/src/context/turn_aborted.rs:34](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/core/src/context/turn_aborted.rs#L34) |
| `subagent_notification` | `<subagent_notification>` … closing tag | [core/src/context/subagent_notification.rs:34-36](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/core/src/context/subagent_notification.rs#L34-L36) |
| `recommended_plugins` | `<recommended_plugins>` … closing tag | [core/src/context/recommended_plugins_instructions.rs:43](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/core/src/context/recommended_plugins_instructions.rs#L43) |

Later `role: "user"` messages in a subagent's rollout stay `user`: the
parent's v1 `send_input` tool submits plain user input to the child
([core/src/agent/control.rs:134-143](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/core/src/agent/control.rs#L134-L143)), and a person can also type into a subagent thread, because the TUI's
`/subagents` picker makes it the active thread and composer input is sent
to the active thread ([tui/src/multi_agents.rs:1-5](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/tui/src/multi_agents.rs#L1-L5), [tui/src/app/thread_routing.rs:475-497](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/tui/src/app/thread_routing.rs#L475-L497)). The rollout records both alike.

A copied fork has no boundary beyond the ancestor's `session_meta` and the
per-message `inherited_user_message` flag, so the other copied records stay
in the fork's file under the fork's session id.

Expected rows from the sample below: `system` session start, `system`
`task_started`, `system` `developer: ...`, `system`
`context: environments.environment_context: ...`, `user` "run the tests",
`tool_use` `exec_command` (`call_1`), `tool_result` `[exit 1] 1 failing`
(the `CommandExecution` item has id `call_1`, so it adds only the exit
code), `thinking` "one test fails" with `--include-thinking`, `assistant`,
`system` `task_complete`, `system`
`agent message /root -> /root/tester: rerun only the failing test`, and
a `system` row carrying the cut last line in full. The `UserMessage` item and the
`token_usage_record` give no row.

Sample rollout, paginated shape
(`.codex/sessions/2026/10/02/rollout-2026-10-02T11-00-00-0199b2c3-1111-7aaa-8bbb-000000000001.jsonl`):

```json
{"timestamp":"2026-10-02T09:00:00.000Z","ordinal":0,"type":"session_meta","payload":{"session_id":"0199b2c3-1111-7aaa-8bbb-000000000001","id":"0199b2c3-1111-7aaa-8bbb-000000000001","timestamp":"2026-10-02T09:00:00.000Z","cwd":"/srv/proj","originator":"codex-tui","cli_version":"0.150.0","source":"cli","thread_source":"user","model_provider":"openai","history_mode":"paginated","git":{"commit_hash":"0a1b2c3d","branch":"main"}}}
{"timestamp":"2026-10-02T09:00:01.000Z","ordinal":1,"type":"event_msg","payload":{"type":"task_started","turn_id":"0199b2c3-2222-7aaa-8bbb-000000000001","started_at":1790931601,"model_context_window":272000,"collaboration_mode_kind":"default"}}
{"timestamp":"2026-10-02T09:00:01.100Z","ordinal":2,"type":"response_item","payload":{"type":"message","id":"m1","role":"developer","content":[{"type":"input_text","text":"<permissions instructions>sandboxed</permissions instructions>"}]}}
{"timestamp":"2026-10-02T09:00:01.200Z","ordinal":3,"type":"turn_context","payload":{"turn_id":"0199b2c3-2222-7aaa-8bbb-000000000001","cwd":"/srv/proj","approval_policy":"on-request","sandbox_policy":{"type":"workspace-write"},"model":"gpt-5.5-codex","summary":"auto"}}
{"timestamp":"2026-10-02T09:00:01.300Z","ordinal":4,"type":"response_item","payload":{"type":"message","id":"m2","role":"user","content":[{"type":"input_text","text":"<environment_context>\n<cwd>/srv/proj</cwd>\n</environment_context>"}],"internal_chat_message_metadata_passthrough":{"turn_id":"0199b2c3-2222-7aaa-8bbb-000000000001","content_item_kinds":["environments.environment_context"]}}}
{"timestamp":"2026-10-02T09:00:01.400Z","ordinal":5,"type":"response_item","payload":{"type":"message","id":"m3","role":"user","content":[{"type":"input_text","text":"run the tests"}],"internal_chat_message_metadata_passthrough":{"turn_id":"0199b2c3-2222-7aaa-8bbb-000000000001","content_item_kinds":["user.text"]}},"metadata":{"client_authored":true,"user_input_order":0}}
{"timestamp":"2026-10-02T09:00:01.500Z","ordinal":6,"type":"event_msg","payload":{"type":"item_completed","thread_id":"0199b2c3-1111-7aaa-8bbb-000000000001","turn_id":"0199b2c3-2222-7aaa-8bbb-000000000001","item":{"type":"UserMessage","id":"u1","content":[{"type":"text","text":"run the tests","text_elements":[]}]},"started_at_ms":1790931601500,"completed_at_ms":1790931601500}}
{"timestamp":"2026-10-02T09:00:03.000Z","ordinal":7,"type":"response_item","payload":{"type":"function_call","id":"fc1","name":"exec_command","arguments":"{\"cmd\":\"npm test\"}","call_id":"call_1"}}
{"timestamp":"2026-10-02T09:00:06.000Z","ordinal":8,"type":"response_item","payload":{"type":"function_call_output","call_id":"call_1","output":"1 failing"}}
{"timestamp":"2026-10-02T09:00:06.100Z","ordinal":9,"type":"event_msg","payload":{"type":"item_completed","thread_id":"0199b2c3-1111-7aaa-8bbb-000000000001","turn_id":"0199b2c3-2222-7aaa-8bbb-000000000001","item":{"type":"CommandExecution","id":"call_1","command":["npm","test"],"cwd":"/srv/proj","parsed_cmd":[],"source":"agent","status":"failed","aggregated_output":"1 failing","exit_code":1},"started_at_ms":1790931603000,"completed_at_ms":1790931606000}}
{"timestamp":"2026-10-02T09:00:07.000Z","ordinal":10,"type":"response_item","payload":{"type":"reasoning","id":"rs1","summary":[{"type":"summary_text","text":"one test fails"}],"encrypted_content":"gAAAA"}}
{"timestamp":"2026-10-02T09:00:08.000Z","ordinal":11,"type":"response_item","payload":{"type":"message","id":"m4","role":"assistant","phase":"final_answer","content":[{"type":"output_text","text":"One test fails in src/a.test.ts."}]}}
{"timestamp":"2026-10-02T09:00:08.100Z","ordinal":12,"type":"token_usage_record","payload":{"thread_id":"0199b2c3-1111-7aaa-8bbb-000000000001","turn_id":"0199b2c3-2222-7aaa-8bbb-000000000001","session_id":"0199b2c3-1111-7aaa-8bbb-000000000001","root_turn_id":"0199b2c3-2222-7aaa-8bbb-000000000001","response_id":"resp_1","usage":{"input_tokens":900,"cached_input_tokens":0,"output_tokens":40,"reasoning_output_tokens":10,"total_tokens":940}}}
{"timestamp":"2026-10-02T09:00:08.200Z","ordinal":13,"type":"event_msg","payload":{"type":"task_complete","turn_id":"0199b2c3-2222-7aaa-8bbb-000000000001","last_agent_message":"One test fails in src/a.test.ts.","started_at":1790931601,"completed_at":1790931608,"duration_ms":7200}}
{"timestamp":"2026-10-02T09:00:09.000Z","ordinal":14,"type":"inter_agent_communication","payload":{"author":"/root","recipient":"/root/tester","other_recipients":[],"content":"rerun only the failing test","trigger_turn":true}}
this line is cut mid-wri
```

`history.jsonl`:
`{"session_id":"0199b2c3-1111-7aaa-8bbb-000000000001","ts":1790931601,"text":"run the tests"}`

## Confidence

High: file layout and naming, envelope, the written type set and the
legacy/paginated split, `session_meta`, `turn_context` and `ResponseItem`
field names, timestamp formats and units, `history.jsonl` and
`session_index.jsonl` shapes (source, and the local tabulation agrees for
every type it contains). Medium: that copied forks can contain an
ancestor's `session_meta` (inferred from the metadata sync guard, not from a
file); the exact payload of `item_completed` for item kinds not seen locally
(read from the structs, not from files); `AgentPath` string form in the
sample (`/root/...` is illustrative). Not determined: pre-envelope rollouts
from the earliest releases; whether `local_shell_call_output` exists (the
parser lists it but `ResponseItem` has no such variant at this commit; it
is harmless); how often the harness emits `agent_message` response items
versus `inter_agent_communication` lines. The `state_5.sqlite` and
`thread_history_1.sqlite` columns and `item_json` shapes are from the
migrations and structs at [3e23877](https://github.com/openai/codex/commit/3e238776e857eccd3bde6bff3026e2e9798f6524) (high); the table and column names agree
with the Windows install of [section 1](#1-evidence), whose values were not
read, so the rows rest on a synthetic fixture (medium for the times'
pairing with the rollout, which no real install has shown).
