# codex-cli

OpenAI's Codex CLI (catalog agent `codex-cli`), the Rust `codex-rs` workspace, writes one
append-only JSONL transcript per thread, which Codex calls a rollout, under `~/.codex`: each line an
envelope around a tagged item, plus a global prompt history. The same code runs behind the VS Code
extension and, as Codex Desktop, inside the ChatGPT desktop app (see
[`chatgpt-desktop.md`](chatgpt-desktop.md)); the standalone CLI and the desktop app share one
`~/.codex` and one login. Open Interpreter is a fork that keeps the format byte for byte under
`~/.openinterpreter` ([`open-interpreter.md`](open-interpreter.md), which records only what
differs), and Ollama's `ollama launch` writes files into `~/.codex`
([Files written by Ollama](#files-written-by-ollama)). The agent is parsed by
`doubleagent/parsers/codex.py` (`CodexParser`, built on the shared `RolloutParser`). The TUI below
is the CLI's terminal user interface.

## 1. Source and evidence

[openai/codex](https://github.com/openai/codex), Apache-2.0, open source, shallow clone at
`scratchpad/repos/codex`, HEAD
[`3e238776e857eccd3bde6bff3026e2e9798f6524`](https://github.com/openai/codex/commit/3e238776e857eccd3bde6bff3026e2e9798f6524)
(2026-10-03). Paths below are relative to `codex-rs/`. All claims are **source** (file:line under
`codex-rs/`) unless marked **local** (names-only listing of `~/.codex` on this host, the
development-host install under [Observed](#observed); every schema claim is from source unless so
marked) or **web** (community write-ups used only for the desktop app). Statements marked
**observed** come from the real installs under [Observed](#observed).

Confidence per claim. High: file layout and naming, envelope, the written type set and the
legacy/paginated split, `session_meta`, `turn_context` and `ResponseItem` field names, timestamp
formats and units, `history.jsonl` and `session_index.jsonl` shapes (source, and the local
tabulation agrees for every type it contains). Medium: that copied forks can contain an ancestor's
`session_meta` (inferred from the metadata sync guard, not from a file); the exact payload of
`item_completed` for item kinds not seen locally (read from the structs, not from files);
`AgentPath` string form in the sample (`/root/...` is illustrative). Not determined: pre-envelope
rollouts from the earliest releases; whether `local_shell_call_output` exists (the parser lists it
but `ResponseItem` has no such variant at this commit; it is harmless); how often the harness emits
`agent_message` response items versus `inter_agent_communication` lines. The `state_5.sqlite` and
`thread_history_1.sqlite` columns and `item_json` shapes are from the migrations and structs at
[3e23877](https://github.com/openai/codex/commit/3e238776e857eccd3bde6bff3026e2e9798f6524) (high);
the table and column names agree with the Windows install under [Observed](#observed), whose values
were not read, so the rows rest on a synthetic fixture (medium for the times' pairing with the
rollout, which no real install has shown).

### Observed

- macOS, Codex Desktop inside ChatGPT 26.1013.40934 (issues 49, the ChatGPT desktop parser, 149, and
  160, the resume and sync question): ChatGPT `26.1013.40934` (bundle identifier `com.openai.codex`,
  the build after the 26.1007.71326 of the 2026-10-15 round) with the bundled Codex
  `0.163.0-alpha.10.2` (`originator` `Codex Desktop`; `cli_version` 0.162.0-alpha.17.2 on
  2026-10-15), observed from 2026-10-18 18:15Z to 2026-10-19 00:43Z in the macOS lab VM of the
  2026-10-15 bullet below (macOS 26.6.2, build 25G83, arm64, one user), one step per listing (names,
  sizes and modification times diffed after each step, so each file below is mapped to the step that
  wrote it), read for file names, sizes, key names, value types, enum values and row counts only;
  the steps and the app's terms (Codex and ChatGPT composer modes, projectless output directory,
  Approve for me and its guardian review threads, Full access, heartbeat, remote control) are in
  [section 1 of `chatgpt-desktop.md`](chatgpt-desktop.md#1-source-and-evidence), and the app's own
  files in [`chatgpt-desktop.md`](chatgpt-desktop.md). Every thread was a Codex-mode thread with a
  rollout under `~/.codex/sessions`: a plain question, a coding task in the project `~/Demo` (later
  resumed after a restart, given a model switch, Approve for me, a full-access turn and two turns
  sent from paired phones), a guardian review thread, and a scheduled task's thread; the plain
  question's thread was then deleted with the app's own command. A reply to a ChatGPT-mode
  conversation wrote nothing under `~/.codex`. The sh collector 1.14.0, run live as the user on
  2026-10-19 (00:43:01Z to 00:43:21Z), attributed 58 manifest rows to `codex-cli`, among them the
  automations, `sqlite/codex-dev.db`, `logs_2.sqlite` and the global state, and found the projects
  `~/Demo` and `~/Documents/Codex/2026-10-18/new-chat`; collector 1.16.0 collects the second as
  `codex-cli` files and no longer takes it for a project (issue 149). What this build adds to
  `~/.codex` is in [macOS, ChatGPT 26.1013.40934](#macos-chatgpt-26101340934).

  Times are UTC. The listings of the first five steps (install to the
  approvals) were taken in the VM's local zone, Eastern Daylight Time
  (UTC-4), and are converted here. Rollout file names and their date
  directories are in local time too, as [section 7](#7-transcript-stores)
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
    ([section 10](#10-other-stores)) and, in `codex-dev.db`
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
    project, with `work` and `outputs` inside. Analyzer 0.18.0 lists
    it in inventory.json under `scratch_directories`, not `projects`: a
    scratch directory is a working directory that belongs to the agent
    rather than to the user, and a project one the user pointed the
    agent at (issue 149). The app wrote no
    `history.jsonl` and no `version.json`; the prompt went to the
    `prompt-history` key of `.codex-global-state.json`
    ([section 10](#10-other-stores)). `session_index.jsonl` got 1 line,
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
    ([section 10](#10-other-stores)): the app server's response rows
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
    its own. `logs_2.sqlite` joins the two ([section 10](#10-other-stores)).
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
    ([section 10](#10-other-stores)).
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
    and `automations/.run-jitter-salt` ([section 10](#10-other-stores))
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
    row ([section 10](#10-other-stores)) and two top-level global-state
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
    the parser reads those records ([section 13](#13-parser-plan)):
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
- Ubuntu, standalone CLI (issues 113, 118): Ubuntu 26.04.1 LTS, Codex CLI 0.162.1 standalone,
  2026-10-15, 17:12Z to 17:22Z (times in UTC), in the author's Ubuntu lab VM (aarch64, kernel
  7.0.0-38-generic, one user; no Node.js, npm, snap or deb package of Codex, and no ChatGPT app,
  which has no Linux build), read for file names, sizes, key names, value types and line counts
  only. The CLI was installed with its shell installer, logged in through the browser flow, and
  given two turns in `~/demo`, which wrote seven files there. `codex --version` prints
  `codex-cli 0.162.1`; the rollout records `originator` `codex-tui` and `source` `vscode`. A fresh
  CLI's `~/.codex` holds only the source-described files: no `sqlite/codex-dev.db`,
  `.codex-global-state.json`, `.desktop-created`, `automations`, `ambient-suggestions`,
  `computer-use`, `visualizations`, `vendor_imports`, `plugins/.plugin-appserver`, `.tmp`,
  `cap_sid`, `node_repl` or `.sandbox*`, which are the desktop app's or Windows'; `config.toml`
  (42 B) holds only `tui.screen_reader_detection_done`. The sh collector from `main` (1.12.0 with
  this round's changes), run live as the user, not root: 1 project (`~/demo`), 39 `codex-cli` files
  (9.9 MiB), 6 excluded, 1 `symlink`, no `error_copy` (the sh collector reads the files the running
  daemon holds open), and 5 `error_read` rows for system accounts' homes the non-root run cannot
  list. The layout is in [Standalone CLI on Linux](#standalone-cli-on-linux).
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
- macOS, Codex Desktop inside ChatGPT and standalone CLI (issues 113, 118, 120, 121): ChatGPT
  `26.1007.71326` (an Electron build, bundle id `com.openai.codex`; see
  [`chatgpt-desktop.md`](chatgpt-desktop.md)) with the bundled Codex `0.162.0-alpha.17.2`
  (`originator` `Codex Desktop`), then Codex CLI `0.162.1` (`originator` `codex-tui`) from its shell
  installer, observed 2026-10-15 (16:25Z to 17:05Z) in the author's macOS lab VM, macOS 26.6.2 build
  25G83, arm64, one user (times in UTC). The user repeated the Windows round; the files were read
  for file names, sizes, key names, value types and row counts only. Four rollouts: a project task
  in `~/Demo`, the target thread of a scheduled automation in
  `~/Documents/Codex/2026-10-15/new-chat`, a thread in the projectless output directory
  `~/Documents/Codex/2026-10-15/e`, and the CLI's one prompt in `~/demo2`. The `~/.codex` tree is
  the Windows one with the differences in [macOS differences](#macos-differences). The sh collector
  from `main` (1.12.0 before the macOS lines), run live as the user, not root, collected 220
  `codex-cli` files (85.8 MiB, 77 MB of it the computer-use app bundle, now excluded, issue 121), 9
  excluded, 1 `symlink`, and found all 4 projects, since `grep` reads rollouts the running app holds
  open. Since collector 1.16.0 the `~/Documents/Codex` output directories are collected as
  `codex-cli` files instead of being discovered as projects (issue 149).
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
    same keys as on Windows ([section 10](#10-other-stores)), `rrule` of the
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
- Windows, standalone CLI (issues 113, 120): Codex CLI `0.162.1` (`originator` `codex-tui`,
  `cli_version` `0.162.1`; TUI is the terminal user interface), installed at 15:38Z on 2026-10-15
  (run until 15:46Z) in the VM of the Codex Desktop bullet below, beside the ChatGPT desktop app,
  with the PowerShell installer OpenAI documents for Windows (the exact command was not recorded).
  No npm, Node.js, winget or scoop is on the host. The user gave it one prompt from a PowerShell
  console in a new folder, `C:\users\<user>\demo-cli` (`~\demo-cli`, typed in lower case). The CLI
  shared the desktop app's `~\.codex` and its login: `auth.json` was not rewritten, no login was
  asked for and no second credential file appeared. Its one rollout (106,200 B, 47 lines) records
  `source` `vscode` like the desktop app's, so `originator` is what tells them apart. The run hit a
  sandbox setup error (`setup_error.json` code `helper_unknown_error`; the daemon's stderr log
  records a failed process creation and a failed file write in the project folder); what the folder
  ended up holding was not surveyed. The console's own command history is in PSReadLine's
  `ConsoleHost_history.txt`, which is shell history, the job of the EDR (the endpoint detection and
  response tool), and not collected. Collector 1.12.0 from `main` before the changes of this round,
  run at 15:48Z after the CLI had exited: 57 collected, 9 excluded, 1 too large, 2 `symlink`, 4
  `error_copy`, and 1 project, `C:\users\<user>\demo-cli`, read from the CLI's closed rollout; the
  three desktop rollouts were still held open (issue 114). What the standalone install writes is in
  [Standalone CLI on Windows](#standalone-cli-on-windows).

  Its rollout (`rollout-2026-10-15T11-41-45-<uuid>.jsonl`, 106,200 bytes, 47 lines: `session_meta`
  1, `turn_context` 1, `world_state` 1, `response_item` 20, `event_msg` 18, `token_usage_record` 6,
  0 bad lines) names `originator` `codex-tui`, `cli_version` `0.162.1`, and `source` `vscode`, as
  the desktop app's do; its `session_meta.payload` has the same keys as the desktop rollouts,
  `creator_user_id` and `creator_account_id` included. The parser gave 31 rows: 2 `user`, 2
  `assistant`, 9 tool calls with their results (`exec` 5, `node_repl.js` 2, `shell` 1, `apply_patch`
  1; `node_repl.js` is a tool of the `node_repl` MCP (Model Context Protocol) server the app's
  `config.toml` configures), `task_started` 15:42:43Z to `task_complete` 15:43:59Z (75,943 ms),
  `model: gpt-6.1-sol` (a third model id), and a `permission mode:` row with the granular approval
  object (`request_permissions` and `mcp_elicitations` true, the rest false) and the
  `workspace-write` sandbox. The sandbox failed to start a process during the run
  (`.sandbox/setup_error.json` `code` `helper_unknown_error`), so some tool calls failed. The CLI
  also wrote `history.jsonl`, which the desktop app had not: one line with `session_id`, `text` and
  `ts`, the shape of [section 10](#10-other-stores). The console commands that started it are in
  PowerShell's own history file, which is shell history and left to the EDR (the endpoint detection
  and response tool).
- Windows, Codex Desktop inside ChatGPT (issues 113, 114, 115, 116, 118): the ChatGPT desktop app
  `26.1007.9446.0` (the Microsoft Store package `OpenAI.Codex`, an MSIX package, the Windows app
  package format; see [`chatgpt-desktop.md`](chatgpt-desktop.md)) bundles Codex, which identifies
  itself in its rollouts as `originator` `Codex Desktop`, `cli_version` `0.162.0-alpha.17.2`; the
  desktop app's own database records `app_version` `26.1007.71326`, `build_flavor` `prod`. Observed
  2026-10-15 in the author's Parallels lab VM, Windows 11 ARM64 (the 64-bit Arm architecture; `ver`
  reports `10.0.26300.9550`), one user, times in UTC, read for file names, sizes, key names, value
  types, enum values and row counts only; no listing was taken between tasks, so the mapping from
  task to file is by modification time only. The bundled Codex uses the standard `CODEX_HOME`,
  `~\.codex` (`~` is `%USERPROFILE%`), created at first launch: 9,155 files, most of them plugin and
  skill copies under `.tmp\`, `plugins\cache\` and `skills\.system\`. Two local threads were run
  (two rollouts, one in the app's default output directory and one in a project folder), a ChatGPT
  chat with an image generation, which left no rollout, and a failed automation, which left nothing;
  later the same day (survey at 15:30Z) a ChatGPT Plus subscription (the paid plan; only a token
  refresh and a longer `models_cache.json`), a saved scheduled automation, which wrote
  `automations/` and a third rollout on a different model, and a GitHub connection, which wrote
  nothing locally. Not exercised: a resumed thread, a denied tool call, an "allow always" grant, a
  model switch within a thread, remote control, an automation run. Collector 1.12.0 from `main`
  before the changes of this round collected `~\.codex` as `codex-cli`: 34 files collected, 8
  `skipped_excluded`, 1 `skipped_size`, 3 `error_copy` (`.sqlite-maintenance.lock` and two
  `thread-writer-locks\<uuid>.lock`, byte-range locked by the running app), and no project, because
  the PowerShell reader could not open the rollouts the app held (issue 114). What the desktop app
  adds to `~\.codex` is in
  [Codex Desktop inside the ChatGPT app](#codex-desktop-inside-the-chatgpt-app).
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
  - `session_meta.payload` keys: `id`, `session_id`, `timestamp`, `cwd`, `runtime_workspace_roots`
    (1 entry), `originator` `Codex Desktop`, `cli_version`, `source` `vscode`, `thread_source`
    `user`, `model_provider` `openai`, `base_instructions` (`text`, and `provenance` with `type`
    `model` and `model`), `history_mode` `paginated`, `context_window` (`window_id`),
    `creator_user_id` (29 characters) and `creator_account_id` (36 characters, a UUID). Every
    top-level key is in the source list in [section 8](#8-record-schema);
    `base_instructions.provenance` is observed, not checked against source at
    [3e23877](https://github.com/openai/codex/commit/3e238776e857eccd3bde6bff3026e2e9798f6524). No
    `git` block (neither directory was a repository). `source` is `vscode` for these desktop
    threads, so `originator` is the key that names the desktop app.
  - `turn_context.payload` keys: `turn_id`, `root_turn_id`, `cwd`, `workspace_roots` (2),
    `current_date`, `timezone`, `approval_policy` `on-request`, `sandbox_policy` (`type`
    `workspace-write`, `writable_roots`, `network_access`, `exclude_tmpdir_env_var`,
    `exclude_slash_tmp`), `permission_profile` (`type` `managed`, `file_system` with `type`
    `restricted` and 13 `entries`, `network` `restricted`), `model` `gpt-6-luna`,
    `collaboration_mode` (`mode` `default`, `settings` with `model`, `reasoning_effort` `medium` and
    `developer_instructions`), `effort` `medium`, `summary` `detailed`, `personality` `friendly`.
    Observed and not among the fields [section 8](#8-record-schema) lists from source at
    [3e23877](https://github.com/openai/codex/commit/3e238776e857eccd3bde6bff3026e2e9798f6524)
    (whether that commit's struct already has them was not rechecked): `disabled_plugin_ids`,
    `approvals_reviewer` `user`, `active_permission_profile` (`id` `:workspace`),
    `file_system_sandbox_policy` (`kind` `restricted`, 13 `entries`), `comp_hash`,
    `multi_agent_version` `v2`, `realtime_active`, `cyber_access_program` `standard`. The parser
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
    ([section 10](#10-other-stores)) and `.codex-global-state.json`. A first
    attempt to create a scheduled automation failed in the app and wrote
    nothing.
  - Later the same day (third survey 15:30Z), after the account was
    subscribed to ChatGPT Plus, the user created a scheduled automation
    that saved, and connected a GitHub account. The automation wrote
    `automations/<slug>/automation.toml` and one `codex-dev.db`
    `automations` row ([section 10](#10-other-stores)), and at once created
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
  - Not exercised: a resumed thread, a denied tool call, an "allow
    always" grant, a model switch within a thread, subagents, an
    automation run. The macOS round of 2026-10-18 above exercised all
    of them but the grant and a subagent the agent spawned itself.
- Local: the real install on the development host, Codex 0.160.0
  (`session_meta.cli_version`), one rollout of 20 lines, a 1-line
  `history.jsonl` and a 1-line `session_index.jsonl`, plus scratchpad copies
  of `state_5.sqlite` and `thread_history_1.sqlite`. Only record types, key
  paths, value types and enum values were tabulated; no content was read
  into this document. The one rollout is `history_mode: "paginated"` and
  has no `git` block, so the legacy event set and `git` are source only. The databases were
  opened only from scratchpad copies, and only for table names, row counts and key names.

### Source reviews

- 2026-10-19: [openai/codex](https://github.com/openai/codex)
  at [`4e7b9e2`](https://github.com/openai/codex/commit/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857),
  the head of `main` on 2026-10-19, compared file by file with
  [`3e23877`](https://github.com/openai/codex/commit/3e238776e857eccd3bde6bff3026e2e9798f6524),
  the commit the rest of this document cites, by diffing the two trees.
  Source only; nothing was installed or run. One line per class, the
  detail in [section 2](#2-per-user-storage) for paths,
  [section 10](#10-other-stores),
  [section 11](#11-format-versions) and
  [section 13](#13-parser-plan):
  - Permission state: found, not read. Standing grants in `rules/default.rules` (a prefix rule
    appended for each "approve and remember" answer, a network rule for each network allow or deny),
    in `config.toml` (`approval_policy`, `sandbox_mode`, `approvals_reviewer`,
    `default_permissions`, a project's `trust_level`, and `approval_mode = "approve"` for each MCP
    or app tool approved for good), both collected by the `codex-cli|.codex` line
    ([Standing grants](#standing-grants)), and the per-call records of the new `state_5.sqlite`
    table `guardian_review_feedback` and of the `PatchApproval` and `RequestPermissionsResponse` log
    lines. The parser reads none of them.
  - Model: no new file; already covered; `turn_context.model` and the `thread_settings_applied`
    snapshot are unchanged at HEAD.
  - Past use beyond the rollouts: found, not read: the memories pipeline's
    `memories/rollout_summaries/*.md`, `raw_memories.md` and `memories_1.sqlite` `stage1_outputs`
    (off by default), the thread goals in `goals_1.sqlite` and the rollout's `thread_goal_updated`
    events, and the SQLite recovery copies under `db-backups/`. The memories files and `db-backups/`
    were already listed among the paths; what each holds is in [section 10](#10-other-stores).
  - Sync, relay and origin: no new file; already covered; unchanged at HEAD. A `/feedback` report
    with logs now also attaches the thread's failed automatic reviews as
    `auto-review-failures.jsonl`.
  - Scratch directories: found. The worktrees Codex makes for a thread sit in
    `<CODEX_HOME>/worktrees/<4 hex>/<repository name>`, or under the absolute path in `config.toml`
    `[desktop] git-worktree-root`; the analyzer's catalog rule classes the first, not the second
    ([Scratch directories](#scratch-directories)).
  - Deletion: found. `thread/delete` removes the rollouts (live and archived, plain and compressed),
    the `session_index.jsonl` lines, the thread's rows in `state_5.sqlite`,
    `thread_history_1.sqlite`, `queue_1.sqlite`, `goals_1.sqlite` and the memories databases, and
    the `logs_2.sqlite` rows whose `thread_id` is the thread; it leaves `history.jsonl`, the
    memories files until the next consolidation, and `db-backups/` ([Deletion](#deletion)).
  - Version drift: found. Paths: the paths of [section 2](#2-per-user-storage) are unchanged at HEAD
    except two moved source files; no path in this document disappeared. The `secrets/` lock file is
    written by `login/src/oauth_session_storage.rs`
    ([21-25](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/login/src/oauth_session_storage.rs#L21-L25)),
    which replaced `gateway_auth_storage.rs`; the directory and file names are unchanged. The agent
    message board database moved to `ext/agent-message-board/src/local/pool.rs`
    ([16](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/ext/agent-message-board/src/local/pool.rs#L16)),
    same file name. Records: `turn_context` no longer carries `network` (the parser's `network=`
    field reads `-` for new rollouts); `task_started` `turn_attribution`, which the parser already
    reads from the desktop app's rollouts, is now in source; the `op=ExecApproval` log line prints
    an opaque decision word; the record envelope, `RolloutItem`, `SessionMeta`, `ResponseItem` and
    the database file names are unchanged. The parser keeps working on HEAD's rollouts.
  - Credentials: no new credential file was found: the quoted file names ending `.age`, `.json`,
    `.lock`, `.toml` or `.env` in `codex-rs/login`, `codex-rs/secrets`, `codex-rs/rmcp-client` and
    `codex-rs/cli` differ between the two commits only by a configuration file name, not a
    credential store.
  - Project path: a rollout `cwd` inside a thread worktree (`.codex/worktrees/...` by default) is a
    scratch directory, not a project ([Scratch directories](#scratch-directories)); `config.toml`
    `[projects."<path>"]` keys name trusted and untrusted projects.
  - Bad lines: not a collector concern; one parser gap at the time of the review: a
    `thread_history_1.sqlite` row whose `item_json` did not decode was counted in one summary row
    instead of one row per record carrying it. Fixed since ([Bad lines](#bad-line-rows)).

## Collection

### 2. Per-user storage

Home resolution: `CODEX_HOME` if set (must exist, canonicalised) else `dirs::home_dir()/.codex`
([utils/home-dir/src/lib.rs:13-56](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/utils/home-dir/src/lib.rs#L13-L56)).
No OS branching: Linux, macOS and Windows all use `~/.codex` / `%USERPROFILE%\.codex`. The macOS
desktop app uses the same `~/.codex` for sessions (web: github issue 49797, jazzyalex write-up) and
keeps only Sparkle update state in `~/Library/Application Support/com.openai.codex`
([cli/src/doctor/updates.rs:586](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/cli/src/doctor/updates.rs#L586)).
Since 26.1007 the bundle id `com.openai.codex` is the ChatGPT app, which bundles Codex (observed on
macOS, 2026-10-15), so that directory is collected as `chatgpt-desktop` (issue 121).

Inside `$CODEX_HOME`:

- `sessions/YYYY/MM/DD/rollout-<YYYY-MM-DDThh-mm-ss>-<thread-uuid>.jsonl` transcripts
  ([rollout/src/lib.rs:86](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/rollout/src/lib.rs#L86),
  [rollout_file_name.rs:51-67](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/rollout/src/rollout_file_name.rs#L51-L67),
  [recorder.rs:1733-1734](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/rollout/src/recorder.rs#L1733-L1734),
  [list.rs:905-916](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/rollout/src/list.rs#L905-L916));
  may be zstd-compressed `.jsonl.zst`
  ([rollout/src/compression.rs:29](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/rollout/src/compression.rs#L29),[68](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/rollout/src/compression.rs#L68),[98](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/rollout/src/compression.rs#L98)).
  `archived_sessions/` same layout
  ([rollout/src/lib.rs:87](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/rollout/src/lib.rs#L87)).
  `session_index.jsonl`
  ([rollout/src/session_index.rs:20](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/rollout/src/session_index.rs#L20)).
  Local confirms `sessions/2026/10/03/rollout-*.jsonl`.
- `history.jsonl` prompt history
  ([message-history/src/lib.rs:52](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/message-history/src/lib.rs#L52),[86](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/message-history/src/lib.rs#L86)).
- SQLite: `state_5.sqlite` (threads, metadata), `logs_2.sqlite`, `goals_1.sqlite`,
  `memories_1.sqlite`, `queue_1.sqlite`, `thread_history_1.sqlite`
  ([state/src/sqlite.rs:34-39](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/state/src/sqlite.rs#L34-L39)),
  `agent_message_board_1.sqlite`
  ([ext/agent-message-board/src/local.rs:55](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/ext/agent-message-board/src/local.rs#L55)),
  with `-wal`/`-shm` sidecars (local). Recovery copies in `db-backups/sqlite-<n>/`
  ([state/src/runtime/recovery.rs:16](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/state/src/runtime/recovery.rs#L16)).
- `memories/` (`MEMORY.md`, `rollout_summaries/*.md`), `memories_v2/`, `memories_extensions/`
  ([memories/read/src/lib.rs:14](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/memories/read/src/lib.rs#L14),
  [memories/write/src/control.rs:5-7](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/memories/write/src/control.rs#L5-L7),[56-63](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/memories/write/src/control.rs#L56-L63)).
  - Source review of 2026-10-19 at
    [`4e7b9e2`](https://github.com/openai/codex/commit/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857),
    not seen on a real install: the memories pipeline (off by default,
    [features/src/lib.rs:1303-1305](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/features/src/lib.rs#L1303-L1305))
    writes `memories/rollout_summaries/<stem>.md`, `memories/raw_memories.md`, `memories/MEMORY.md`
    and `memories/memory_summary.md`, and `memories_1.sqlite` and `memories_v2_1.sqlite`
    ([memories/write/src/lib.rs:39-40](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/memories/write/src/lib.rs#L39-L40),
    [state/src/sqlite.rs:43](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/state/src/sqlite.rs#L43),
    [114-119](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/state/src/sqlite.rs#L114-L119)).
    Collected.
- `log/` (`codex-tui.log`, `codex-login.log`)
  ([core/src/config/mod.rs:4093](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/core/src/config/mod.rs#L4093),
  [tui/src/lib.rs:281](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/tui/src/lib.rs#L281),
  [cli/src/login.rs:85](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/cli/src/login.rs#L85)).
  Daemon logs in `app-server-daemon/`
  ([feedback/src/daemon_logs.rs:18](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/feedback/src/daemon_logs.rs#L18));
  `app-server-control/` socket dir
  ([app-server-transport/src/transport/mod.rs:53](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/app-server-transport/src/transport/mod.rs#L53)).
- `shell_snapshots/`
  ([core/src/shell_snapshot.rs:107](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/core/src/shell_snapshot.rs#L107)),
  `skills/` with bundled `skills/.system/`
  ([skills/src/lib.rs:57](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/skills/src/lib.rs#L57)),
  `plugins/` and `plugins/cache/`
  ([core-plugin-common/src/installed.rs:11](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/core-plugin-common/src/installed.rs#L11)),
  `packages/` managed binaries
  ([app-server-daemon/src/managed_install.rs:52](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/app-server-daemon/src/managed_install.rs#L52)),
  `worktrees/`
  ([worktree/src/settings.rs:44](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/worktree/src/settings.rs#L44)),
  `visualizations/`
  ([tui/src/inline_visualization.rs:93](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/tui/src/inline_visualization.rs#L93)),
  `.tmp/`
  ([rollout/src/maintenance.rs:27](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/rollout/src/maintenance.rs#L27),
  [core-plugins/src/startup_sync.rs:171](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/core-plugins/src/startup_sync.rs#L171);
  `.tmp/bundled-marketplaces/`), `tmp/arg0/`
  ([arg0/src/lib.rs:363](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/arg0/src/lib.rs#L363)),
  `cache/`
  ([tui/src/pets/ambient.rs:158](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/tui/src/pets/ambient.rs#L158)),
  `installation_id`
  ([core/src/installation_id.rs:17](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/core/src/installation_id.rs#L17)),
  `version.json`
  ([cli/src/doctor/updates.rs:35](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/cli/src/doctor/updates.rs#L35)),
  `.sandbox_migration`
  ([execpolicy/src/sandbox_migration.rs:10](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/execpolicy/src/sandbox_migration.rs#L10)),
  `config.toml`
  ([config/src/lib.rs:52](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/config/src/lib.rs#L52)),
  `rules/` exec policy
  ([core/src/exec_policy.rs:54](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/core/src/exec_policy.rs#L54)),
  `hooks.json`, `agents/`.
- Windows sandbox: `.sandbox/` (logs `.sandbox/logs/sandbox.<date>.log`, `setup_error.json`),
  `.sandbox-bin/`, `.sandbox-secrets/`
  ([windows-sandbox-rs/src/spawn_prep.rs:108](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/windows-sandbox-rs/src/spawn_prep.rs#L108),
  [logging.rs:240-251](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/windows-sandbox-rs/src/logging.rs#L240-L251),
  [setup.rs:196](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/windows-sandbox-rs/src/setup.rs#L196),
  [uninstall_windows.rs:132-137](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/windows-sandbox-rs/src/uninstall_windows.rs#L132-L137)).
- Local only (not grepped in source): `models_cache.json`, `thread-writer-locks/`,
  `tui-thread-reference-capabilities/`, `.sqlite-maintenance.lock`; the first two are described
  under [Codex Desktop inside the ChatGPT app](#codex-desktop-inside-the-chatgpt-app).

#### Scratch directories

- `Documents/Codex/<date>/<slug>/{work,outputs}` (`~\Documents\Codex\<date>\<slug>\` on Windows):
  the ChatGPT desktop app's projectless output directory, the working directory the bundled Codex is
  given for a thread with no project, which the thread's rollout `cwd` names; `outputs/` holds the
  files the agent wrote for the user. Collected whole since collector 1.16.0 by the
  `codex-cli|Documents/Codex` catalog line and attributed to `codex-cli`, with the exclusions, the
  size limit and the secret globs applying as everywhere; project discovery drops a rollout `cwd` in
  it ([section 6](#6-where-the-project-path-is-recorded)). Observed on Windows (ChatGPT
  26.1007.9446.0, 2026-10-15;
  [section 2 of `chatgpt-desktop.md`](chatgpt-desktop.md#2-per-user-storage)) and on macOS
  (2026-10-15 and 2026-10-18; [Observed](#observed)); not seen on the Ubuntu install, which ran the
  standalone CLI only. The Windows install has not yet had a per-step round, so which action creates
  the directory is known only from the macOS listings. The catalog line is tried against every home,
  so an install that writes the directory has it collected and one that does not is unaffected
  (issue 149).

From the source review of 2026-10-19 at
[`4e7b9e2`](https://github.com/openai/codex/commit/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857); not
seen on a real install: the git worktrees Codex creates for a thread are
`<CODEX_HOME>/worktrees/<first 4 hex of a uuid>/<repository name>` unless `config.toml`
`[desktop] git-worktree-root` names another absolute path
([worktree/src/settings.rs:12-13](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/worktree/src/settings.rs#L12-L13),
[43-56](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/worktree/src/settings.rs#L43-L56),
[worktree/src/paths.rs:13-30](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/worktree/src/paths.rs#L13-L30));
`[desktop] worktree-auto-cleanup-enabled`, on by default, lets Codex remove them
([settings.rs:62-70](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/worktree/src/settings.rs#L62-L70)).
The default location is under the `.codex/worktrees` exclusion, so the catalog walk records it as
one `skipped_excluded` row. Project discovery is a different matter: `find_cli_session_projects`
drops only a rollout `cwd` under `Documents/Codex`, so a thread that ran in a worktree has that
worktree discovered as a project and its project files collected, and the same holds for a
configured root outside the home. The analyzer classes a worktree under `.codex` as a scratch
directory and one under a configured root as a project. The thread that owns a worktree is in
`codex-thread.json` (`version`, `ownerThreadId`) inside the source repository's per-worktree git
directory
([worktree/src/metadata.rs:19-27](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/worktree/src/metadata.rs#L19-L27),
[88-91](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/worktree/src/metadata.rs#L88-L91)),
which no catalog line names. The other scratch directory is the desktop app's projectless output
directory under `Documents/Codex`, above.

#### Files written by Ollama

Written by Ollama, not by Codex (Ollama source at `v0.35.1`, commit
[`b0c1ca4f7549d7acdfa52a7dcffc934bc63a43ce`](https://github.com/ollama/ollama/commit/b0c1ca4f7549d7acdfa52a7dcffc934bc63a43ce);
detail in [ollama.md](ollama.md) [section 5](ollama.md#5-project-local-files)). Ollama always uses
`<home>/.codex` and ignores `CODEX_HOME`
([`cmd/launch/codex.go:234-240`](https://github.com/ollama/ollama/blob/b0c1ca4f7549d7acdfa52a7dcffc934bc63a43ce/cmd/launch/codex.go#L234-L240)).

- `ollama launch chatgpt` (the ChatGPT desktop app's Codex, macOS and Windows) writes
  `ollama-launch-codex-routing.json` and `ollama-launch-models.json`
  ([`internal/proxy/codex_desktop.go:32-38`](https://github.com/ollama/ollama/blob/b0c1ca4f7549d7acdfa52a7dcffc934bc63a43ce/internal/proxy/codex_desktop.go#L32-L38),
  [`cmd/launch/codex_app.go:952-958`](https://github.com/ollama/ollama/blob/b0c1ca4f7549d7acdfa52a7dcffc934bc63a43ce/cmd/launch/codex_app.go#L952-L958)),
  rewrites `config.toml` (root `model`, `model_catalog_json`, `openai_base_url` pointing at
  `<ollama host>/api/codex/v1`; `profile` and `model_provider` removed; `[desktop]` reasoning
  efforts extended,
  [`codex_app.go:312-354`](https://github.com/ollama/ollama/blob/b0c1ca4f7549d7acdfa52a7dcffc934bc63a43ce/cmd/launch/codex_app.go#L312-L354)),
  and creates `auth.json` when none exists ([section 3](#3-credentials)). The previous `config.toml`
  and catalogs are copied to `~/.ollama/backup/codex-app/`, which the `ollama` catalog line
  collects.
- `ollama launch codex` (the CLI) writes `model.json` and `ollama-launch.config.toml` and leaves
  `config.toml` alone
  ([`codex.go:209-232`](https://github.com/ollama/ollama/blob/b0c1ca4f7549d7acdfa52a7dcffc934bc63a43ce/cmd/launch/codex.go#L209-L232),[`250-268`](https://github.com/ollama/ollama/blob/b0c1ca4f7549d7acdfa52a7dcffc934bc63a43ce/cmd/launch/codex.go#L250-L268)).

All of these sit under `.codex` and are collected by the `codex-cli|.codex` line; none is excluded.

#### Codex Desktop inside the ChatGPT app

Observed on the Windows install above, not in the source at
[3e23877](https://github.com/openai/codex/commit/3e238776e857eccd3bde6bff3026e2e9798f6524) unless a
citation says otherwise. Names, types and counts only; no value from the install is recorded.

- `.desktop-created` (0 B, written at first launch) and `.codex-provisioning-<16 hex>.guard` (0 B):
  markers that the desktop app created and provisioned this home.
- `installation_id` (36 B), `.sandbox_migration` (3 B), `.sqlite-maintenance.lock` (0 B, byte-range
  locked while the app runs).
- `.codex-global-state.json` and `.codex-global-state.json.bak` (61,390 B each): the desktop app's
  UI and account state. Top-level keys include `local-projects` (project id to
  `{createdAt, id, name, rootPaths, updatedAt}`), `thread-project-assignments`,
  `thread-workspace-root-hints` and `thread-projectless-output-directories` (thread id to an
  absolute path), `projectless-thread-ids`, `selected-project`,
  `app-server-projects-migration-by-host`, `desktop-first-seen-at-ms` and
  `electron-persisted-atom-state`. Under the last: `chatgpt-conversation-resume-tokens-v1` (keyed by
  a JSON array of the account's user id and a ChatGPT conversation id; each value
  `{expiresAtMs, promptMessageId, token, turnTraceId}`, the token 419 characters),
  `client-thread-bindings-v1` (`client-new-thread:<uuid>` and `local-chatgpt:<uuid>` keys, the
  second binding a ChatGPT chat), `prompt-history` (per thread and `global`,
  `[{document, markdown}]`: the user's prompts), `composer-recent-model-configurations-v1`
  (`{model, reasoningEffort, serviceTier}`), `heartbeat-thread-permissions-by-id` (thread id to
  `{activePermissionProfile, approvalPolicy, approvalsReviewer, sandboxPolicy}`),
  `mcp-global-entrypoints-v2`, `recent-workspace-files-v3` (one entry per file a thread wrote, keyed
  by a JSON array whose last element spells a Windows path as `win32:/mnt/c/...`),
  `external-agent-import-discovery:claude-code,claude-cowork` and `...:cursor` (the app looks for
  Claude Code, Claude Cowork and Cursor state to import; empty results on the install),
  `electron:onboarding-welcome-v2-role-state` (`completedConversationalOnboardingTaskId`, `roles`,
  `workMode`) and `cloud-pet-artwork-cache` (`accountId`, `userId`). After a Plus subscription and
  an automation it gained `chatgpt-work-model-settings-v1`,
  `chatgpt-work-models-v1/<user id>/<workspace uuid>` (the account's user and workspace ids in the
  key), `fast-mode-personalized-estimate`, `seen-model-upgrade-list` and a
  `thread-reference-capability:<uuid>` per new thread (123,250 B). Flagged secret
  ([section 3](#3-credentials)).
- `sqlite/codex-dev.db` with a WAL sidecar (write-ahead log, where SQLite holds recent writes): the
  desktop app's own database. Tables: `local_thread_catalog` (one row per thread the app lists:
  `host_id`, `thread_id`, `display_title`, `cwd`, `source_kind`, `thread_source`, `model_provider`,
  `git_branch`, `project_id`, `conversation_origin` and more; the two local threads had
  `source_kind` `vscode` and a `cwd`, the ChatGPT chat one row with `source_kind` `chatgpt` and only
  its title; after the second round 5 rows, three local threads and two `chatgpt` rows, one with
  `conversation_origin` `tpp`, a token not determined that also appears in the package's
  `.codex-tpp-local-executor-installation-id` file name), `local_thread_catalog_hosts` (`host_id`,
  `host_kind`: `local` and `chatgpt:<workspace uuid>:<user id>`), `automations` (`name`, `prompt`,
  `status`, `rrule`, `cwds`, `model`, `next_run_at`, `account_id`, `user_id` and more) and
  `automation_runs` (`thread_id`, `automation_id`, `status`, `source_cwd`, `inbox_title`,
  `inbox_summary`, `archived_user_message`, `archived_assistant_message`), both empty after the
  failed first attempt (the saved automation is described below), `inbox_items`,
  `live_visualization_suggestions`, `thread_timeline_ledger`, `local_app_server_feature_enablement`
  and `codex_schema_migrations` (33 rows with `app_version`, `build_flavor`, `build_commit`).
  Collected; the analyzer's `chatgpt-desktop` parser reads its `chatgpt` rows
  ([`analyzer/research/chatgpt-desktop.md`](chatgpt-desktop.md)).
- `state_5.sqlite` (the source-described thread store) gains, on this build, `projects`,
  `project_roots` (`project_id`, `position`, `path`), `project_idempotency_keys`, `thread_sections`,
  `remote_control_enrollments` and `external_agent_config_imports` tables, and `threads` columns
  `project_id`, `originator`, `creator_user_id` and `creator_account_id` among others.
  `thread_history_1.sqlite` `thread_items` holds one row per turn item (`item_type` values
  `agentMessage`, `commandExecution`, `fileChange`, `reasoning`, `userMessage`, `webSearch`), and
  `logs_2.sqlite` `logs` 2,156 rows from the app server.
- `plugins/.plugin-appserver/` (`codex.exe`, 282,678,064 B, and `codex-code-mode-host.exe`,
  `codex-command-runner.exe`, `codex-windows-sandbox-setup.exe`, 7 to 70 MB): copies of the
  package's binaries. Excluded from collector 1.12.0 (issue 116); before that change the three
  smaller ones were collected and `codex.exe` was `skipped_size`.
  `plugins/.remote-plugin-install-staging/` (empty) is excluded with it.
- `.tmp/bundled-marketplaces/openai-bundled/` (`.materialization-key`, `plugins/`, 274 MB) and
  `.tmp/plugins/` (60 plugin directories, 57 MB; the whole `.tmp/` was gone by the second survey, so
  it is a temporary tree), the marketplace sync the source cites
  ([core-plugins/src/startup_sync.rs:171](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/core-plugins/src/startup_sync.rs#L171));
  `cache/remote_plugin_catalog/<16 hex>.json` (36 MB), `cache/codex_apps_tools/` and
  `cache/codex_apps_server_info/`; `plugins/cache/` with `openai-bundled`, `openai-curated-remote`
  and `openai-primary-runtime` (149 MB). All under existing exclusions.
- `automations/` (observed after a scheduled automation was created in the app, 2026-10-15):
  `.run-jitter-salt` (37 B) and one directory per automation, named by a slug made from the name the
  user typed (user content), holding `automation.toml` (383 B) with the keys `version` (int), `id`
  (str, the slug), `kind` (str, `heartbeat`), `name` (str), `prompt` (str), `status` (str,
  `ACTIVE`), `rrule` (str, an iCalendar recurrence rule of the form
  `RRULE:FREQ=WEEKLY;BYHOUR=9;BYMINUTE=0;BYDAY=MO,TU,WE,TH,FR`), `target_thread_id` (str, a thread
  uuid), `created_at` and `updated_at` (int, epoch milliseconds). The same automation is a row in
  `sqlite/codex-dev.db` `automations` with `status`, `kind`, `rrule`, `next_run_at` and
  `next_run_nominal_at` (epoch ms), `last_run_at` null, `cwds` (an empty JSON array),
  `target_thread_id` and `auto_archive` 0, the other columns null; `automation_runs` (one row per
  run, linking `thread_id` and `automation_id`) and `inbox_items` stayed empty because the
  automation had not fired. Creating it created its target thread at once: a third rollout with its
  `cwd` in a new `~/Documents/Codex/<date>/new-chat/` output directory, one user turn and one
  assistant message, and with it a `thread-writer-locks` lock, a `visualizations` directory and a
  `session_index.jsonl` line. Collected.
- `ambient-suggestions/<40 hex>/ambient-suggestions.json` (139 B, observed): `currentSuggestionIds`
  (array), `generatedAtMs` (number), `projectRoot` (str, an absolute path) and `suggestions`
  (array), both arrays empty on the install; governed by `desktop.ambient-suggestions-enabled` in
  `config.toml`. Collected.
- `computer-use/config.json` (152 B: `accentColor`, `direction`, `locale`, `strings`),
  `vendor_imports/skills-curated-cache.json` (1,267 B: `fetchedAt`, `skills`), `models_cache.json`
  (177,581 B: `client_version`, `etag`, `fetched_at`, `identity`, `models` with each model's
  instructions template and confirmation policies for browser and computer use): collected.
- `thread-writer-locks/` (`.coordination.lock` and one `<thread uuid>.lock` per thread, 0 B, the
  thread locks byte-range locked while the app runs), `project-metadata-locks/` (empty),
  `visualizations/<yyyy>/<mm>/<dd>/<thread uuid>/` (empty, excluded), `code-review-plugin/` and
  `pets/` (empty).
- `.sandbox/` (`deny_read_acl_state.json`, `sandbox.<date>.log`, `sandbox-<16 hex>.log`,
  `setup_marker.json`, excluded), `.sandbox-bin/` (empty, excluded) and
  `.sandbox-secrets/sandbox_users.json` ([section 3](#3-credentials)), and
  `tmp/arg0/codex-arg0<6 chars>/` (`apply_patch.bat`, `applypatch.bat`, excluded).
- `config.toml` as the app writes it: `notify`, a `[desktop]` table (`followUpQueueMode`,
  `conversationDetailMode`, `ambient-suggestions-enabled`), `marketplaces.openai-bundled` and
  `marketplaces.openai-primary-runtime` (`source_type` `local`),
  `plugins.<id>@openai-bundled.enabled` and `plugins.<id>@openai-primary-runtime.enabled` entries,
  an `mcp_servers.node_repl` server with its `env`, and `windows.sandbox` `elevated`.

The Windows sandbox, which the source describes
([setup.rs:196](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/windows-sandbox-rs/src/setup.rs#L196)),
was set up during onboarding: it created two enabled local accounts, `CodexSandboxOffline` and
`CodexSandboxOnline`, whose passwords are in `.sandbox-secrets/sandbox_users.json`, and the package
runs a service `CodexSandboxService.OpenAI.Codex`. The accounts and the service are the EDR's view
(the endpoint detection and response tool) and are not collected.

Outside `~/.codex` the app keeps copies of the binaries in `%LOCALAPPDATA%\OpenAI\Codex` and a
1.27 GB runtime in `~/.cache/codex-runtimes`, neither collected; see [section 4 of
`chatgpt-desktop.md`](chatgpt-desktop.md#4-exclusions).

#### Standalone CLI on Windows

Observed with Codex CLI 0.162.1 from the PowerShell installer ([section 1](#1-source-and-evidence));
names, types and sizes only.

- `~\.codex\packages\standalone\`: `install.lock` (0 B), `auto-update-version` (31 B, one token),
  `current` (an NTFS junction, a directory reparse point, to
  `releases\0.162.1-aarch64-pc-windows-msvc`) and that release: `bin\codex.exe` (282,434,864 B),
  `bin\codex-code-mode-host.exe` (69,820,208 B), `codex-package.json` (216 B: `entrypoint`,
  `layoutVersion`, `pathDir`, `resourcesDir`, `target`, `variant`, `version`), `codex-path\rg.exe`,
  and `codex-resources\` with `codex-command-runner.exe`, `codex-windows-sandbox-setup.exe` and
  `voice\` (`bin\codex-voice-host.exe` with GStreamer, GLib, Opus and PCRE2 libraries,
  `manifest.json`, `runtime.json`, `sources.json`, `windows-crt.json`, licences). File times inside
  the release are the build's (2026-10-09). The `packages/` directory the source names
  ([app-server-daemon/src/managed_install.rs:52](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/app-server-daemon/src/managed_install.rs#L52)).
- `~\.codex\packages\app-server-daemon\`: the same layout with the same binaries, fetched by the
  daemon's updater.
- `%LOCALAPPDATA%\Programs\OpenAI\Codex\bin`: a junction to
  `~\.codex\packages\standalone\current\bin`, which the installer adds to the user `Path` value in
  `HKCU\Environment` (the current user's environment variables in the registry). No Start Menu entry
  and no Uninstall registry key.
- `~\.codex\app-server-daemon\`: the CLI runs the app server as a daemon that outlives the TUI.
  `daemon.lock`, `daemon.pid.lock`, `daemon-updater.pid.lock` (0 B), `daemon.pid` (328 B, JSON:
  `executableIdentity.{digest, path_digest}` as arrays of 32 numbers, `pid`, `processStartTime`),
  `daemon-updater.pid` (52 B: `pid`, `processStartTime`), `daemon.stderr.log` (Rust `tracing` lines
  with ANSI colour codes, `<ISO 8601 time> ERROR codex_core::tools::router: error=...`),
  `daemon-updater.stderr.log` (JSON lines with `timestampMs`, `processPid`, `stage`
  (`installer_fetch`, `installer_run`), `outcome`, `elapsedMs`, `failure`, or `event`
  `package_selected` with `details.{release, trigger}`), `daemon-updater.sock` and an empty
  `workdir\`. `~\.codex\app-server-control\` holds `app-server-control.sock` and
  `app-server-startup.lock` (0 B). The two `.sock` files are Unix domain sockets, which NTFS stores
  as reparse points with the tag `0x80000023` (`IO_REPARSE_TAG_AF_UNIX`); the PowerShell collector
  records each as a `symlink` row whose `target` is the socket's own extended-length path (issue
  120).
- `cap_sid` (419 B, JSON): `readonly`, `workspace`, `workspace_by_cwd` (a map from a `c:\...` path
  to a string) and `writable_root_by_path` (two `c:\...` paths to strings): capability SIDs by
  workspace path (SIDs are Windows security identifiers; a capability SID has the form
  `S-1-15-3-...`), inferred from the key names and value lengths, not from a value. Collected, not
  flagged.
- `version.json` (105 B: `dismissed_version`, `last_checked_at`, `latest_version`), the CLI's update
  check, cited in the source list above; `history.jsonl` (one line: `session_id`, `text`, `ts`), the
  CLI's prompt history, which the desktop app had not written;
  `tui-thread-reference-capabilities\<thread uuid>` (0 B, one per TUI thread);
  `node_repl\active_execs\` (empty), the scratch of the `node_repl` MCP server that `config.toml`
  configures (MCP is the Model Context Protocol, through which an agent calls external tools).
- `.sandbox\` gained `setup_error.json` (77 B: `code`, `message`) and a longer `sandbox.<date>.log`;
  `.sandbox-bin\` gained the sandbox's own copies of `codex.exe` and
  `codex-command-runner-0.162.0-alpha.17.2.exe` (289,784,416 B together).
- `config.toml` was rewritten at install (43 B longer; its keys were not re-read). `auth.json`,
  `.codex-global-state.json` and the desktop app's automation were not changed by the CLI.

#### macOS differences

Observed on the macOS install of [section 1](#1-source-and-evidence); names, types and sizes only.
Everything else in [Codex Desktop inside the ChatGPT app](#codex-desktop-inside-the-chatgpt-app) and
[Standalone CLI on Windows](#standalone-cli-on-windows) was present in the same form (`auth.json`,
`config.toml`, `.codex-global-state.json`, the SQLite stores, `sqlite/codex-dev.db`, `automations/`,
`ambient-suggestions/`, `vendor_imports`, `history.jsonl`, `version.json`, `app-server-daemon/`,
`app-server-control/`).

- `plugins/.plugin-appserver/codex-cli/` (337,674,240 B): on macOS the copied binaries sit in a
  `codex-cli` subdirectory; the `.codex/plugins/.plugin-appserver` exclusion covers it.
- `computer-use/Codex Computer Use.app` (bundle id `com.openai.sky.CUAService`, version
  26.1005.1001425, 168 files, 76,615,353 B), the computer-use agent's app, beside
  `computer-use/config.json`. Excluded with `.codex/computer-use/*.app` (issue 121); before that it
  was collected whole.
- `ipc/ipc.sock` (a Unix domain socket) and an empty `shell_snapshots/` (2026-10-15; on 2026-10-18
  it held the two most recent snapshots of each live thread, see
  [macOS, ChatGPT 26.1013.40934](#macos-chatgpt-26101340934)), macOS only.
- No `.sandbox`, `.sandbox-bin` or `.sandbox-secrets`: the Windows sandbox accounts have no macOS
  counterpart. The macOS sandbox is Seatbelt (Apple's sandbox profile mechanism), which left no file
  that was observed. `.sandbox_migration` is present.
- `app-server-daemon/daemon.pid` (472 B) and `daemon-updater.pid` (194 B) carry a `processIdentity`
  object (`bootId`, a uuid, `startSeconds`, `startMicroseconds`, `uniqueId`) that the Windows files
  lack.
- `app-server-control/app-server-control.sock` is a real symlink here, to
  `/private/tmp/codex-daemon-<uid>/<64 hex>`, and gets a correct `symlink` row.
  `app-server-daemon/daemon-updater.sock` and `ipc/ipc.sock` are sockets and get no manifest row
  (issue 120).
- The standalone CLI: `packages/standalone/releases/0.162.1-aarch64-apple-darwin/` and
  `packages/app-server-daemon/releases/0.162.1-aarch64-apple-darwin/` (`bin/`, `codex-path/`,
  `codex-resources/`, `codex`, `codex-package.json`), each with a `current` symlink, 676,267,646 B
  in all, one `skipped_excluded` row under `.codex/packages`. The installer adds the symlinks
  `~/.local/bin/codex` and `~/.local/bin/codex-code-mode-host` into
  `packages/standalone/current/bin`, which no catalog line names, and a block in `~/.zprofile`
  between `# >>> Codex installer >>>` and `# <<< Codex installer <<<` that prepends `~/.local/bin`
  to `PATH`; shell startup files are not collected. The daemon processes ran from the
  `app-server-daemon` release.

#### macOS, ChatGPT 26.1013.40934

Observed on the macOS install of 2026-10-18 ([section 1](#1-source-and-evidence)), bundled Codex
`0.163.0-alpha.10.2`; names, types and sizes only. Everything in [Codex Desktop inside the ChatGPT
app](#codex-desktop-inside-the-chatgpt-app) and [macOS differences](#macos-differences) was present,
with these additions and observations:

- Before sign-in `~/.codex` already held `.codex-global-state.json` (1,282 B), `config.toml`
  (2,114 B), `installation_id` (36 B), `.sqlite-maintenance.lock`, `ipc/ipc.sock`,
  `tmp/arg0-macos/codex-arg0*/`, `vendor_imports/skills-curated-cache.json`, `.tmp/`, `plugins/`,
  `skills/.system/`, `computer-use/Codex Computer Use.app`, `sqlite/codex-dev.db`, `state_5.sqlite`,
  `logs_2.sqlite`, `goals_1.sqlite`, `memories_1.sqlite` and `queue_1.sqlite`. Sign-in wrote
  `auth.json` (4,299 B), `models_cache.json` (399,712 B), `.sandbox_migration` (3 B), the first
  shell snapshot and the first `ambient-suggestions` file. No `history.jsonl` or `version.json` was
  written all round: the desktop app keeps prompts in the global state's `prompt-history`.
  `thread_history_1.sqlite` was created with the first thread.
- `shell_snapshots/<thread uuid>.<unix ns>.sh` (2,135 to 2,299 B, 43 lines): the snapshot the source
  writes
  ([core/src/shell_snapshot.rs:107](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/core/src/shell_snapshot.rs#L107)),
  written anew at each resume and turn of a thread while older ones are removed (the two most recent
  per thread remained at the end of the round, and a quit removed every snapshot of threads not
  reopened); the name is the thread id and a Unix time in nanoseconds. The content is the user's
  login-shell environment replayed for the sandbox ([section 3](#3-credentials)). Flagged secret
  from collector 1.15.0.
- `thread-writer-locks/<uuid>.lock` can exist for a thread that never wrote anything: at the resume
  (2026-10-18 21:46:13Z) and when the scheduled task was created (23:18:39Z to 23:18:41Z) the app
  prewarmed a guardian review session (`startup_prewarm` with the model `codex-auto-review` in
  `logs_2.sqlite`) whose id got a 0-byte lock and no rollout, `state_5.sqlite` `threads` row,
  `session_index.jsonl` line or `thread_history_1.sqlite` rows. A lock is not a session. Quitting
  the app removed the locks of threads that were not open.
- Rollout file names and their date directories use the Mac's local time, while every timestamp
  inside the rollout is UTC: the scheduled task's thread, started at 23:18:38Z, is
  `sessions/2026/10/18/rollout-2026-10-18T19-18-38-<uuid>.jsonl` on a host at UTC-4.
- `automations/.run-jitter-salt` (37 B) and `automations/<slug>/automation.toml` (356 B; the slug is
  the kebab-case of the task's name), with the keys of
  [Codex Desktop inside the ChatGPT app](#codex-desktop-inside-the-chatgpt-app). Here `rrule` was
  `RRULE:FREQ=WEEKLY;BYHOUR=19;BYMINUTE=45;BYDAY=SU,MO,TU,WE,TH,FR,SA` for a task the user set to
  daily, the hour in local time. The task's `sqlite/codex-dev.db` `automations` row carries
  `account_id`, `user_id` and `installation_id`, `last_run_at`, and `next_run_at` offset from
  `next_run_nominal_at` by the jitter. A Run now and a scheduled run both reported into the task's
  target thread; neither wrote an `automation_runs` or `inbox_items` row (the scheduled run decided
  not to notify the user).
- `cache/remote_plugin_catalog/<16 hex>.json` (38,747,166 B, downloaded at each launch),
  `cache/codex_apps_server_info/<40 hex>.json` (189 B) and `cache/codex_apps_tools/<40 hex>.json`
  (825,347 B): under the excluded `.codex/cache`, which was 39.6 MB in the live run.
- `config.toml` gains a `[projects."<path>"]` table with `trust_level` `trusted` when a project
  folder is added. Neither the model nor the permission mode (Approve for me, Full access) is
  written to it.
- `state_5.sqlite` on this build also has `guardian_review_feedback`,
  `external_agent_config_imports`, `thread_spawn_edges` and `thread_read_receipts`.
  `remote_control_enrollments` holds one row once remote control is enabled: `websocket_url`,
  `account_id`, `app_server_client_name`, `server_id`, `environment_id`, `server_name` (the Mac's
  host name), `updated_at` and `remote_control_enabled`, which turning connections off sets to 0
  without removing the row.
- `.codex-global-state.json` grew from 1,282 B before sign-in to 120,989 B by the remote-control
  step. After remote control was enabled it gained the top-level keys
  `electron-local-remote-control-environment-id` and `codex-mobile-has-connected-device`. After a
  thread was deleted it kept the keys naming that thread (its prompts, description, permissions and
  activity time) and gained `codex-writing-block-deleted-thread-v1:<uuid>`, a deletion marker.
- A delete with the app's own command removed the thread's rollout, its `session_index.jsonl` line
  and its rows in `state_5.sqlite`, `thread_history_1.sqlite` and `sqlite/codex-dev.db`; no
  `archived_sessions/` directory was created. `logs_2.sqlite` kept the thread's rows.
- Outside `~/.codex`: `~/.cache/codex-runtimes/codex-primary-runtime/` (32,625 entries), and sockets
  under `/private/tmp/codex-browser-use/` and `/private/tmp/codex-app-tools/`, replaced at each
  launch; none is collected.

#### Standalone CLI on Linux

Observed on the Ubuntu install of [section 1](#1-source-and-evidence); names, types and sizes only.

- `~/.codex/packages/standalone/` and `~/.codex/packages/app-server-daemon/` (816,297,770 B
  together, one `skipped_excluded` row): `install.lock`, `auto-update-version` (34 B), a `current`
  symlink to `releases/0.162.1-aarch64-unknown-linux-musl` and that release (`bin/`, a `codex`
  symlink into `bin`, `codex-path/`, `codex-resources/`, `codex-package.json`). The target triple
  says the Linux build is statically linked against musl, a C library.
- `~/.local/bin/codex`, a symlink to `~/.codex/packages/standalone/current/bin/codex` (no
  `codex-code-mode-host` link, unlike macOS), and a block in `~/.bashrc` between
  `# >>> Codex installer >>>` and `# <<< Codex installer <<<` that prepends `~/.local/bin` to
  `PATH`, as macOS got in `~/.zprofile`. Neither is collected. No `~/.config/codex`,
  `~/.local/share/codex`, `~/.local/state/codex` or `~/.cache/codex*` exists: the CLI uses
  `~/.codex` only, and `~/.cache/codex-runtimes` belongs to the desktop app.
- The daemon runs from the `app-server-daemon` release and listens on a socket
  `/tmp/codex-daemon-<uid>/<64 hex>` with a `.lock` beside it;
  `~/.codex/app-server-control/app-server-control.sock` is a symlink to it (recorded as a `symlink`
  row with that target). `app-server-daemon/daemon.pid` and `daemon-updater.pid` carry
  `processIdentity.{bootId, startTicks}` on Linux, against `startSeconds`, `startMicroseconds` and
  `uniqueId` on macOS and no `processIdentity` on Windows. `daemon.stderr.log` held one
  `rmcp::transport::streamable_http_client` error line, and `daemon-updater.stderr.log` the JSON
  lines seen on Windows.
- The Linux sandbox is bubblewrap (a tool that runs a process in its own namespaces):
  `/tmp/codex-bwrap-synthetic-mount-targets-<uid>/lock` appeared with the first turn.
- `log/codex-login.log` (544 B, mode 0600): four `tracing` lines of the browser login, from
  `codex_cli::login: starting browser login flow` through the `codex_login::server` callback line
  (`has_code`, `has_state`, `has_error`, `state_valid`) and the token exchange's issuer, token
  endpoint and redirect URI, to `oauth token exchange succeeded`. Source-cited above
  ([cli/src/login.rs:85](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/cli/src/login.rs#L85)).
- Otherwise the source-described files: `auth.json`, `config.toml`, `installation_id`,
  `version.json`, `.sandbox_migration`, `.sqlite-maintenance.lock`, `history.jsonl` (one line per
  turn), `session_index.jsonl`, the SQLite stores with WAL sidecars, `models_cache.json`, `cache/`,
  `plugins/cache/openai-curated-remote` and `plugins/.remote-plugin-install-staging`,
  `skills/.system`, `tmp/`, an empty `shell_snapshots/`, `thread-writer-locks/.coordination.lock`
  and `tui-thread-reference-capabilities/<thread uuid>`.

#### Standing grants

From the source review of 2026-10-19 at
[`4e7b9e2`](https://github.com/openai/codex/commit/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857); not
seen on a real install.

- `rules/default.rules`: Starlark lines (Starlark is the Python-like configuration language of
  Codex's exec policy) appended when the user approves a command and asks Codex to remember it,
  `prefix_rule(pattern=[...], decision="allow")`, and when the user allows or denies a network host,
  `network_rule(host=..., protocol=..., decision=...)`
  ([core/src/exec_policy.rs:54-56](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/core/src/exec_policy.rs#L54-L56),
  [874-876](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/core/src/exec_policy.rs#L874-L876),
  [execpolicy/src/amend.rs:65-80](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/execpolicy/src/amend.rs#L65-L80),
  [85-124](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/execpolicy/src/amend.rs#L85-L124)).
  Collected, not excluded, no credential. The same `rules/` directory in a project's `.codex/` is a
  project file ([section 5](#5-project-local-files)).
- `config.toml` standing grants: `approval_policy`, `sandbox_mode`, `approvals_reviewer`,
  `default_permissions`, `[projects."<path>"] trust_level` and `approval_mode = "approve"` under a
  tool of `mcp_servers`, `plugins` or `apps` once the user approved that tool for good
  ([config/src/config_toml.rs:195-239](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/config/src/config_toml.rs#L195-L239),
  [473](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/config/src/config_toml.rs#L473),
  [core/src/mcp_tool_call.rs:2394-2457](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/core/src/mcp_tool_call.rs#L2394-L2457)).
  Collected.
- Started by another agent with approvals bypassed (Agent Zero source review of 2026-10-19, at
  [`ff2a5b9`](https://github.com/agent0ai/agent-zero/commit/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a)):
  Agent Zero's Orchestrator plugin, which tells that agent how to drive other coding CLIs on the
  host or in its container, defaults Codex to `bypass_sandbox: true` and runs
  `codex exec --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox`
  ([`plugins/_orchestrator/default_config.yaml:7-37`](https://github.com/agent0ai/agent-zero/blob/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a/plugins/_orchestrator/default_config.yaml#L7-L37),
  [`plugins/_orchestrator/README.md:86`](https://github.com/agent0ai/agent-zero/blob/ff2a5b9c9c4e490ba38dd7c313e779510bb2071a/plugins/_orchestrator/README.md#L86)).
  Such a thread is an ordinary rollout in Codex's own store; the plugin's permission settings are in
  [section 13 of `analyzer/research/agent-zero.md`](agent-zero.md#13-parser-plan).

#### Deletion

From source at
[`4e7b9e2`](https://github.com/openai/codex/commit/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857). A
`thread/delete` request (the TUI and the desktop app both go through the app server) refuses a
thread whose rollout a fork still references, then removes, for the thread and its spawned
subagents: the rollout under `sessions/` and under `archived_sessions/`, both the `.jsonl` and the
`.jsonl.zst` form, and the thread's `session_index.jsonl` lines
([app-server/src/request_processors/thread_delete.rs:31-63](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/app-server/src/request_processors/thread_delete.rs#L31-L63),
[thread-store/src/local/delete_thread.rs:95-136](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/thread-store/src/local/delete_thread.rs#L95-L136),
[204-281](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/thread-store/src/local/delete_thread.rs#L204-L281));
its `thread_history_1.sqlite` rows
([thread-store/src/local/thread_history.rs:242](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/thread-store/src/local/thread_history.rs#L242));
its agent message boards
([core/src/thread_manager.rs:484-496](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/core/src/thread_manager.rs#L484-L496));
and the `logs_2.sqlite` rows whose `thread_id` column is the thread, its queued items, its memories
`stage1_outputs` row, its goal, and its `state_5.sqlite` rows in `thread_dynamic_tools`,
`thread_spawn_edges`, `thread_read_receipts` and `threads`
([state/src/runtime/threads.rs:1166-1216](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/state/src/runtime/threads.rs#L1166-L1216)).
Neither handler touches `history.jsonl` (grepped
[`delete_thread.rs`](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/thread-store/src/local/delete_thread.rs)
and
[`thread_delete.rs`](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/app-server/src/request_processors/thread_delete.rs)
for `history.jsonl` and `message_history`), the memories files (pruned only at the next
consolidation), `db-backups/` or a log row that names the thread only in its text. The macOS round
of 2026-10-18 found `logs_2.sqlite` kept the deleted thread's rows
([macOS, ChatGPT 26.1013.40934](#macos-chatgpt-26101340934)); source deletes only rows whose
`thread_id` column matches, so which rows survived (rows with the id only in their message text,
rows written after the delete, or a build that did not yet delete log rows) was not determined. An
archive (`thread/archive`) moves each rollout into `archived_sessions/` under its own file name,
without the date directories
([thread-store/src/local/archive_thread.rs:67-130](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/thread-store/src/local/archive_thread.rs#L67-L130)).

### 3. Credentials

- `auth.json` with `OPENAI_API_KEY` and OAuth tokens
  ([login/src/auth/storage.rs:47-53](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/login/src/auth/storage.rs#L47-L53),[163](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/login/src/auth/storage.rs#L163)).
  Store mode `AuthCredentialsStoreMode`: `file` (default), `keyring`, `auto`, `ephemeral`
  ([config/src/types.rs:116-124](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/config/src/types.rs#L116-L124)).
  Keyring via `codex-keyring-store`. `ollama launch chatgpt` creates `auth.json` when the file does
  not exist, mode 0600, with `{"OPENAI_API_KEY": "ollama-local-codex", "auth_mode": "apikey"}`; the
  key is a fixed local sentinel that Ollama's proxy refuses to forward to OpenAI, not a credential,
  and `ollama launch chatgpt --restore` deletes the file only while it still holds that value
  ([Ollama `cmd/launch/codex_app.go:561-631`](https://github.com/ollama/ollama/blob/b0c1ca4f7549d7acdfa52a7dcffc934bc63a43ce/cmd/launch/codex_app.go#L561-L631),
  [`internal/proxy/codex_desktop.go:40-42`](https://github.com/ollama/ollama/blob/b0c1ca4f7549d7acdfa52a7dcffc934bc63a43ce/internal/proxy/codex_desktop.go#L40-L42)).
  The `.codex/auth.json` secret glob flags it either way; a flagged `auth.json` with that value
  means the integration was set up while no Codex login existed.
- On Linux (observed, Ubuntu 26.04.1, Codex CLI 0.162.1 standalone, 2026-10-15) the browser login
  wrote the OAuth tokens to `auth.json` (4,302 B) at the moment of the token exchange; the GNOME
  keyring was not used (`~/.local/share/keyrings` held only the stock `login.keyring` and
  `user.keystore`). `log/codex-login.log` names the login endpoints and the callback's flags, never
  a token, and is rightly collected unflagged.
- `.credentials.json`: MCP OAuth token fallback when keyring unavailable
  ([rmcp-client/src/oauth.rs:17](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/rmcp-client/src/oauth.rs#L17),[857](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/rmcp-client/src/oauth.rs#L857);
  [config/src/types.rs:138](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/config/src/types.rs#L138)).
- `secrets/` gateway OAuth and local secrets, age-encrypted (`gateway_oauth.age`, `local.age`,
  `gateway_oauth.lock`)
  ([login/src/gateway_auth_storage.rs:20-24](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/login/src/gateway_auth_storage.rs#L20-L24),
  [secrets/src/local.rs:166](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/secrets/src/local.rs#L166),[587-591](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/secrets/src/local.rs#L587-L591)).
- `.sandbox-secrets/` Windows sandbox tokens
  ([setup.rs:196](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/windows-sandbox-rs/src/setup.rs#L196)).
  Observed with Codex Desktop: `sandbox_users.json` (828 B) with `offline` and `online` objects,
  each `{username, password}`, and `version`: the passwords of the two sandbox accounts. Flagged by
  `.codex/.sandbox-secrets/*`.
- `.codex-global-state.json` and its `.bak` (observed, Codex Desktop only): ChatGPT conversation
  resume tokens under `electron-persisted-atom-state` `chatgpt-conversation-resume-tokens-v1`, the
  account and user ids in `cloud-pet-artwork-cache` and in the token keys, and the user's prompts in
  `prompt-history`. Flagged by `.codex/.codex-global-state.json*` from collector 1.12.0 (issue 115);
  before that, collector 1.12.0 from `main` collected them unflagged.
- `shell_snapshots/<thread uuid>.<unix ns>.sh` (observed on macOS, Codex Desktop 0.163.0-alpha.10.2
  inside ChatGPT 26.1013.40934, 2026-10-18; written by
  [core/src/shell_snapshot.rs:107](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/core/src/shell_snapshot.rs#L107)):
  43 lines, a `# Snapshot file` header, 29 `export NAME=...` lines, 2 aliases, `unalias -a` and
  `setopt` lines, the user's exported login-shell environment replayed for the sandbox. The exported
  names on the clean lab VM included `BROWSER_USE_ACCESS_VERIFYING_IDENTITY`,
  `CODEX_TASK_WORKSPACE_VERIFYING_IDENTITY`, `CODEX_APP_TOOLS_PIPE_PATH`, `SSH_AUTH_SOCK`, `HOME`,
  `USER` and `TMPDIR`, and no key-like name; on a workstation any API key the login shell exports is
  copied into the file. Flagged by `.codex/shell_snapshots/*` from collector 1.15.0 (issue 160);
  collector 1.14.0 collected them unflagged.
- The desktop app's global state also carries the account's ids inside key names (observed on macOS,
  2026-10-18): `chatgpt-work-models-v1/user-<account id>/<uuid>` and the JSON-array keys of
  `new-task-execution-by-account-project`. The file is flagged already.
- Remote control's server token (observed on macOS, 2026-10-18): `logs_2.sqlite` records its refresh
  when connections are turned back on, never the token; `state_5.sqlite`
  `remote_control_enrollments` has no token column, `auth.json` did not change, and no login
  keychain item named after OpenAI, Codex or ChatGPT existed, so where the token is kept was not
  determined.
- `auth.json` as Codex Desktop writes it (observed): `OPENAI_API_KEY` `null`, `auth_mode`,
  `last_refresh` and `tokens` (`access_token`, `id_token`, `refresh_token`, `account_id`).
- `config.toml` can embed `experimental_bearer_token` per provider
  ([model-provider-info/src/lib.rs:149-157](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/model-provider-info/src/lib.rs#L149-L157));
  `env_key` names an env var instead.
- A copy of `auth.json` outside the home (Ollama source review of 2026-10-19, at
  [`6787222`](https://github.com/ollama/ollama/commit/678722224b3d8c2a024a4fa5f530d83ce34db120)):
  `ollama launch chatgpt` copies `~/.codex/auth.json` and `models_cache.json` into a scratch
  `CODEX_HOME`, `ollama-codex-models-*` in the system temp directory, to list Codex's native models,
  and removes it when the command finishes
  ([`cmd/launch/codex_app.go:1480-1495`](https://github.com/ollama/ollama/blob/678722224b3d8c2a024a4fa5f530d83ce34db120/cmd/launch/codex_app.go#L1480-L1495)).
  A crash leaves that copy of the Codex credential in the temp directory, which no catalog line
  covers; see [section 2 of `ollama.md`](ollama.md#2-per-user-storage).

### 4. Exclusions

`.codex/packages`, `.codex/cache`, `.codex/.tmp`, `.codex/tmp`, `.codex/plugins/cache`,
`.codex/plugins/.plugin-appserver` and `.codex/plugins/.remote-plugin-install-staging` (Codex
Desktop, issue 116), `.codex/skills/.system`, `.codex/worktrees`, `.codex/.sandbox`,
`.codex/.sandbox-bin`, `.codex/visualizations`, `.codex/app-server-daemon/packages` (if present).
`.codex/computer-use/*.app` (the computer-use app bundle on macOS, 77 MB, issue 121).

On the Windows standalone install `.codex/packages` (794,201,900 B, the standalone and daemon
releases) and `.codex/.sandbox-bin` (289,784,416 B) each became one `skipped_excluded` row, so the
binaries need no new exclusion; `AppData/Local/Programs/OpenAI/Codex/bin` is a junction into
`.codex/packages` and is not catalogued. On Linux the daemon's socket directory
`/tmp/codex-daemon-<uid>/` and the bubblewrap sandbox's
`/tmp/codex-bwrap-synthetic-mount-targets-<uid>/` are outside the home and named only by the user
id, so no catalog line can hold them.

`.codex/db-backups` is a copy of the state DBs, small, and may hold rows deleted from the live DB:
collect rather than exclude.

In the live run on ChatGPT 26.1013.40934 (macOS, 2026-10-19) the exclusions that fired under
`.codex` were `cache` (39.6 MB, of which `remote_plugin_catalog/` 38.7 MB), `plugins/cache` (67 MB),
`plugins/.plugin-appserver` (341 MB), `plugins/.remote-plugin-install-staging`, `.tmp` (123 MB),
`skills/.system`, `computer-use/Codex Computer Use.app` (78 MB), `tmp` and `visualizations`; nothing
new and large was collected. `Library/Application Support/com.openai.codex` is updater state only,
collected as `chatgpt-desktop` since the macOS round (issue 121).

### 5. Project-local files

`AGENTS.md`, `AGENTS.override.md`
([core/src/agents_md.rs:43-45](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/core/src/agents_md.rs#L43-L45)),
`.codex/config.toml`, `.codex/agents/`, `.codex/hooks.json`, `.codex/hooks/`, `.codex/rules/`,
`.codex/skills/`
([external-agent-migration/src/scope.rs:59-62](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/external-agent-migration/src/scope.rs#L59-L62),
[detect/mod.rs:86](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/external-agent-migration/src/detect/mod.rs#L86),[167](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/external-agent-migration/src/detect/mod.rs#L167),[270](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/external-agent-migration/src/detect/mod.rs#L270);
[exec-server/src/discoverV2/capability_locations.rs:72](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/exec-server/src/discoverV2/capability_locations.rs#L72)),
`.agents/skills`
([external-agent-migration/src/service.rs:467](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/external-agent-migration/src/service.rs#L467)),
`generated_images/` in cwd
([ext/image-generation/src/tool.rs:332](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/ext/image-generation/src/tool.rs#L332)).
No per-project database.

### 6. Where the project path is recorded

- First line of every rollout: `SessionMeta` with `cwd: PathBuf`, `timestamp`, `id`, `originator`,
  `cli_version`, `source`, `runtime_workspace_roots`
  ([protocol/src/protocol.rs:3123-3153](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/protocol.rs#L3123-L3153)).
  Compressed rollouts need zstd before grep.
- `session_index.jsonl`
  ([rollout/src/session_index.rs](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/rollout/src/session_index.rs))
  and `state_5.sqlite` threads table (analyzer).
- Codex Desktop (observed): `state_5.sqlite` `project_roots` `path`; `sqlite/codex-dev.db`
  `local_thread_catalog` `cwd`; and in `.codex-global-state.json`, `local-projects` `rootPaths`,
  `thread-workspace-root-hints` and `thread-projectless-output-directories`. On the install both
  rollouts' `cwd` values named the same directories, so the rollouts, which project discovery
  already reads, are enough; the PowerShell collector read none of them until the fix for issue 114,
  because the running app held them open. On macOS (ChatGPT 26.1013.40934, 2026-10-18) an added
  project is also a `[projects."<path>"]` table in `config.toml`, and collector 1.14.0 took the
  scheduled task's projectless output directory `~/Documents/Codex/2026-10-18/new-chat` from the
  rollouts as a project beside `~/Demo` (issue 149). Since collector 1.16.0 project discovery drops
  a rollout `cwd` that is `<home>/Documents/Codex` or lies under it, and the
  `codex-cli|Documents/Codex` catalog line collects the directory whole instead
  ([section 2](#2-per-user-storage)).

## Parsing

### 7. Transcript stores

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
  ([rollout/src/lib.rs:86-87](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/rollout/src/lib.rs#L86-L87)).
  **Parser reads.**
- `*.jsonl.zst`: zstd level 3, written by a background worker for rollouts idle seven days, in both
  trees
  ([compression.rs:29](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/rollout/src/compression.rs#L29),
  [362-363](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/rollout/src/compression.rs#L362-L363),
  [500-501](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/rollout/src/compression.rs#L500-L501)).
  The worker runs only with the `local_thread_store_compression` feature, which is under development
  and off by default
  ([features/src/lib.rs:1212-1217](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/features/src/lib.rs#L1212-L1217),
  [core/src/thread_manager.rs:461-503](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/core/src/thread_manager.rs#L461-L503)).
  **Parser reads** (needs `zstandard`).
- `.codex/history.jsonl`: one line per submitted prompt, all threads
  ([section 10](#10-other-stores)). **Parser reads.**
- `.codex/session_index.jsonl`: thread renames ([section 10](#10-other-stores)). Not read.
- `.codex/automations/<slug>/automation.toml`: a scheduled automation of
  the ChatGPT desktop app ([section 10](#10-other-stores)). **Parser reads.**
- `.codex/state_5.sqlite`, `.codex/thread_history_1.sqlite`: thread metadata
  and a projection of paginated rollouts ([section 10](#10-other-stores)).
  **Parser reads**, as secondary sources (issue 122).
- **Copies held by other agents.** Three agents copy these transcripts into stores of their own,
  where the copy outlives the original file (source reviews of 2026-10-19; none seen on a real
  install):
  - Hermes Agent's `hermes_cli/foreign_sessions.py` reads Codex's
    `~/.codex/sessions/**/rollout-*.jsonl` and appends their user and assistant turns to its
    `state.db` as a new session whose `origin_json.imported_from` names the tool, the source path
    and the foreign session id, stamped with the import time
    ([`hermes_cli/foreign_sessions.py:254-260`](https://github.com/NousResearch/hermes-agent/blob/86fa9e6ca1de7ee71132d2be0103f3e37d1fa872/hermes_cli/foreign_sessions.py#L254-L260);
    [section 7 of `hermes.md`](hermes.md#7-transcript-stores)).
  - Cline's SDK session import makes an ordinary Cline session with a new id and
    `metadata.importedFrom{tool, sourceSessionId, sourcePath, importedAt, sourceProvider, sourceModel}`;
    at the reviewed commit only Cline's example desktop app calls it
    ([`sdk/packages/core/src/services/session-import/service.ts:349-366`](https://github.com/cline/cline/blob/41e75efc53e7abbcb76564b89e6de57f78659b33/sdk/packages/core/src/services/session-import/service.ts#L349-L366);
    [section 7 of `cline.md`](cline.md#7-transcript-stores)).
  - Pydantic AI's CLAI 2.0 (its command-line chat client) `/resume` copies them into its
    `sessions.db`
    ([`codex_sessions.py:35-37`](https://github.com/pydantic/pydantic-ai/blob/0ba01f92be3fc361f89970502cd6e7dd3611aec3/src/pydantic_clai2/pydantic_clai2/runtime/codex_sessions.py#L35-L37);
    [section 2 of `pydantic-clai.md`](pydantic-clai.md#2-per-user-storage)).
- **Indexed by Zed.** Zed's agent panel can run this agent as an external agent over ACP (the Agent
  Client Protocol, the JSON-RPC protocol Zed uses to drive another agent); its threads sidebar then
  lists the session in `sidebar_threads` with `agent_id` `codex-acp` and the ACP session id in
  `session_id`, while the transcript stays in this agent's own store
  ([`agent_servers/src/custom.rs:17-19`](https://github.com/zed-industries/zed/blob/9cd14daad768fbfaeeac8789f515f9a5f67669a6/crates/agent_servers/src/custom.rs#L17-L19);
  [section 7 of `zed.md`](zed.md#7-transcript-stores)). Whether that id equals the session id this
  agent records was not determined (Zed source review of 2026-10-19).

#### What survives a delete

A `thread/delete` request, which the TUI and the desktop app both send
through the app server, removes the thread's rollouts (live and
archived, plain and compressed), its `session_index.jsonl` lines, its
rows in `state_5.sqlite`, `thread_history_1.sqlite`, `queue_1.sqlite`,
`goals_1.sqlite` and the memories databases, and the `logs_2.sqlite`
rows whose `thread_id` column is the thread
([Deletion](#deletion));
an archive instead moves the rollout into `archived_sessions/`. It
leaves `history.jsonl`, one line per prompt typed into the TUI with the
thread id and its time in seconds (unless `history.persistence` is
`none`, and trimmed oldest-first under `history.max_bytes`), which is
then the one place such a prompt survives. It also leaves the memories
files until the next consolidation, the `db-backups/` copies of a
database Codex found corrupt, and log rows that name the thread only in
their text. On the macOS round of 2026-10-18 the desktop app's delete
was a hard delete that also removed the `codex-dev.db`
`local_thread_catalog` row, while `.codex-global-state.json` kept the
thread's prompts, description, permissions and activity time and gained
the deletion marker `codex-writing-block-deleted-thread-v1:<uuid>`,
and at least one `logs_2.sqlite` row and the empty projectless output
directory remained ([section 1](#1-source-and-evidence)). Hermes Agent, Cline's SDK
and Pydantic AI's CLAI hold copies that outlive the original rollout
([section 7](#7-transcript-stores)). The analyzer reads the archived
rollouts as primary, `history.jsonl` and the global state as secondary
sources (the marker as a `session deleted:` row), and neither the
memories files nor `db-backups/` (see
[Secondary sources](../analyzer/docs/output.md#secondary-sources)).

### 8. Record schema

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

Line types
([history/src/lib.rs:209-227](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/history/src/lib.rs#L209-L227));
which ones are written is decided in
[rollout/src/policy.rs:22-50](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/rollout/src/policy.rs#L22-L50):

| `type` | `payload` | Seen locally |
| --- | --- | --- |
| `session_meta` | thread header, below | yes |
| `turn_context` | per-turn settings, below | yes |
| `response_item` | a Responses API item ([Message content and tool calls](#message-content-and-tool-calls)) | yes |
| `event_msg` | a UI event, tagged by its own `type` (below) | yes |
| `token_usage_record` | `thread_id`, `turn_id`, `session_id`, `root_turn_id`, `response_id`, `usage`, `turn_token_usage`, `thread_token_usage` ([protocol.rs:2263-2273](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/protocol.rs#L2263-L2273)) | yes |
| `world_state` | `full`, `state` (model-visible environment snapshot or patch, [protocol.rs:3272-3278](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/protocol.rs#L3272-L3278)) | yes |
| `compacted` | `message` (the compaction summary), `replacement_history`, window ids ([history/src/lib.rs:285-306](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/history/src/lib.rs#L285-L306), [rollout_payload.rs:238-266](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/history/src/rollout_payload.rs#L238-L266)) | no |
| `inter_agent_communication` | `author`, `recipient`, `other_recipients`, `content` (plain text), `encrypted_content`, `trigger_turn` ([protocol.rs:806-822](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/protocol.rs#L806-L822)) | no |
| `inter_agent_communication_metadata` | `trigger_turn` | no |
| `retained_context` | verified answers and delivered messages for the guardian reviewer ([history/src/retained_context.rs:145-162](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/history/src/retained_context.rs#L145-L162)) | no |
| `security_risk_score` | `scores`, `call_id`, `action`, `sampled_at` ([security_risk.rs:12-25](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/security_risk.rs#L12-L25)) | no |
| `realtime_item` | `id`, `realtime_session_id`, tagged content incl. `transcript_segment` (`role`, `text`); paginated only ([realtime.rs:6-31](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/realtime.rs#L6-L31)) | no |

#### `session_meta`

`session_meta` (line 1;
[protocol.rs:3117-3198](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/protocol.rs#L3117-L3198)):
`id` (this thread), `session_id` (the root thread's id; filled from `id` when absent in old files,
[3243-3269](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/protocol.rs#L3243-L3269)),
`forked_from_id`, `parent_thread_id`, `timestamp`, `cwd`, `runtime_workspace_roots`, `originator`
(`codex-tui` locally), `cli_version`, `source` (`cli`, `vscode`, `exec`, `mcp`, a custom string, or
`{"subagent": ...}`;
[2824-2837](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/protocol.rs#L2824-L2837),
[2905-2923](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/protocol.rs#L2905-L2923)),
`thread_source` (`user`, `subagent`, `guardian_review`, `memory_consolidation` or a feature name;
[2843-2849](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/protocol.rs#L2843-L2849)),
`agent_nickname`, `agent_role`, `agent_path`, `model_provider`, `base_instructions`,
`dynamic_tools`, `memory_mode`, `history_mode` (`legacy` or `paginated`), `history_base`,
`context_window`, and the account fields `creator_user_id`, `creator_account_id`. Beside them, `git`
(`commit_hash`, `branch`, `repository_url`;
[3436-3452](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/protocol.rs#L3436-L3452))
is written only when `cwd` is inside a git repository
([recorder.rs:1978-1990](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/rollout/src/recorder.rs#L1978-L1990)).

#### `turn_context`

`turn_context` (once per user turn and after mid-turn compaction;
[protocol.rs:3296-3358](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/protocol.rs#L3296-L3358)):
`turn_id`, `root_turn_id`, `cwd`, `workspace_roots`, `current_date`, `timezone`, `approval_policy`,
`sandbox_policy`, `permission_profile`, `network`, `model`, `collaboration_mode` (with its own
`settings.model`), `effort`, `summary`, `personality` and more. The four policy fields:
`approval_policy` is a kebab-case string, `untrusted`, `on-request` (the default, also read from the
old `on-failure`) or `never`, or an object `{"granular": {...}}` for per-flow controls
([protocol.rs:986-1009](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/protocol.rs#L986-L1009));
`sandbox_policy` is an object tagged by `type`: `danger-full-access`, `read-only`,
`external-sandbox` or `workspace-write`, the last three with fields of their own
([protocol.rs:1072-1120](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/protocol.rs#L1072-L1120));
`permission_profile`, optional, is an object tagged by `type`: `managed` (`file_system`, `network`),
`disabled` or `external` (`network`)
([models.rs:421-435](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/models.rs#L421-L435));
`network`, optional, is `{allowed_domains, denied_domains}`, two lists of strings
([protocol.rs:3291-3294](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/protocol.rs#L3291-L3294)).

#### `event_msg`

`event_msg` (tagged enum,
[protocol.rs:1352-1358](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/protocol.rs#L1352-L1358)).
Persisted in every mode
([policy.rs:127-139](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/rollout/src/policy.rs#L127-L139)):
`task_started` (`turn_id`, `root_turn_id`, `trace_id`, `started_at` epoch s, `model_context_window`,
`collaboration_mode_kind`), `task_complete` (`turn_id`, `last_agent_message`, `error`, `started_at`,
`completed_at`, `duration_ms`, `time_to_first_token_ms`)
([2152-2197](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/protocol.rs#L2152-L2197);
the wire names are kept from v1,
[1407-1418](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/protocol.rs#L1407-L1418)),
`turn_aborted` (`turn_id`, `reason`, `error`, times;
[4243-4263](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/protocol.rs#L4243-L4263)),
`thread_rolled_back` (`num_turns`;
[3692-3696](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/protocol.rs#L3692-L3696)),
`token_count`, `thread_goal_updated`, `thread_settings_applied`, and `item_completed` (below).
Legacy-mode rollouts also keep `user_message` (`message`, `images`), `agent_message` (`message`,
`phase`), `agent_reasoning` and `agent_reasoning_raw_content` (`text`), `entered_review_mode`,
`exited_review_mode`, `patch_apply_end`, `context_compacted`, `mcp_tool_call_end`, `web_search_end`,
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

#### Message content and tool calls

`response_item.payload` is a `ResponseItem` tagged by snake_case `type`
([protocol/src/models.rs:1010-1256](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/models.rs#L1010-L1256));
all variants but `compaction_trigger` and unknown ones are written
([policy.rs:78-100](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/rollout/src/policy.rs#L78-L100)).
Most variants carry an optional `id` and
`internal_chat_message_metadata_passthrough` (`turn_id`, `create_time` in
fractional epoch seconds, `content_item_kinds`;
[models.rs:954-994](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/models.rs#L954-L994)).

- `message`: `role` (`user`, `assistant`, `developer`; the harness's own instructions go in as
  `developer`), `content[]` of `input_text`, `input_image` (`image_url` or `file_id`), `input_audio`
  or `output_text` blocks, each with `text` where textual
  ([876-896](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/models.rs#L876-L896)),
  and `phase` (`commentary` or `final_answer`;
  [938-952](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/models.rs#L938-L952),
  [1021-1036](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/models.rs#L1021-L1036)).
  A `role: "user"` message is not always typed by the user: the harness injects `AGENTS.md`
  instructions, `<environment_context>`, skill text, subagent notifications, turn-aborted notices
  and user shell commands as user-role messages
  ([core/src/context/contextual_user_message.rs:22-37](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/core/src/context/contextual_user_message.rs#L22-L37)).
  Current versions label each content block in `content_item_kinds`; typed input is `user.text`, the
  environment block `environments.environment_context`
  ([contextual_user_message.rs:51-82](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/core/src/context/contextual_user_message.rs#L51-L82),
  [core/src/context/world_state/environment.rs:200-203](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/core/src/context/world_state/environment.rs#L200-L203)).
  Locally the first turn had three `developer` messages and two `user` messages, of which one was
  `environments.environment_context` and one `user.text`.
- `reasoning`: `summary[]` of `summary_text` (`text`), `content[]` of `reasoning_text` or `text`,
  `encrypted_content`
  ([1048-1060](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/models.rs#L1048-L1060),
  [1982-1993](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/models.rs#L1982-L1993)).
  `content` is written only when it holds `reasoning_text` parts or is null
  ([1624-1631](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/models.rs#L1624-L1631)).
- `function_call`: `name`, `namespace` (MCP and plugin tools), `arguments`
  (a JSON **string**), `call_id`
  ([1074-1093](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/models.rs#L1074-L1093)).
- `custom_tool_call`: `status`, `call_id`, `name`, `namespace`, `input` (free text)
  ([1134-1151](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/models.rs#L1134-L1151)).
  Code mode's `exec` tool
  ([code-mode-protocol/src/lib.rs:52](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/code-mode-protocol/src/lib.rs#L52))
  and the freeform `apply_patch` arrive this way; the one local call was `exec`.
- `local_shell_call`: `call_id`, `status`, `action` (`type: "exec"`, `command` array, `timeout_ms`,
  `working_directory`, `env`, `user`)
  ([1061-1073](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/models.rs#L1061-L1073),
  [1937-1950](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/models.rs#L1937-L1950)).
- `function_call_output`, `custom_tool_call_output`: `call_id`, `name`, `output`, which is a string
  or an array of `input_text`, `input_image`, `input_audio`, `encrypted_content` items
  ([1114-1133](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/models.rs#L1114-L1133),
  [1155-1169](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/models.rs#L1155-L1169),
  [2096-2118](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/models.rs#L2096-L2118),
  [2250-2263](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/models.rs#L2250-L2263)).
  Locally an array of two `input_text` items.
- `web_search_call`: `status`, `action` (`search` with `query`/`queries`, `open_page` with `url`,
  `find_in_page` with `url`, `pattern`)
  ([1191-1204](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/models.rs#L1191-L1204),
  [1952-1980](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/models.rs#L1952-L1980)).
  No output item.
- `tool_search_call` (`call_id`, `execution`, `arguments` object) and `tool_search_output`
  (`call_id`, `status`, `tools[]`)
  ([1094-1108](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/models.rs#L1094-L1108),
  [1170-1182](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/models.rs#L1170-L1182)).
- `agent_message`: `author`, `recipient`, `content[]` of `input_text` or `encrypted_content`
  ([906-911](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/models.rs#L906-L911),
  [1037-1047](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/models.rs#L1037-L1047)).
- `image_generation_call`: `status`, `revised_prompt`, `result` (image data)
  ([1214-1226](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/models.rs#L1214-L1226)).
- `additional_tools` (tool definitions), `compaction` and `context_compaction`
  (`encrypted_content`), `configuration_update`: no readable conversation content
  ([1013-1020](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/models.rs#L1013-L1020),
  [1227-1253](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/models.rs#L1227-L1253)).

The `metadata` sibling on a `response_item` line is harness bookkeeping:
`client_authored`, `retained_source`, `user_input_order`,
`inherited_user_message` (copied from a parent thread), `mcp_attribution`
and others
([history/src/lib.rs:55-135](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/history/src/lib.rs#L55-L135)).

### 9. Joins and timestamps

- **Timestamps.** Line `timestamp` and `session_meta.payload.timestamp`: UTC
  `YYYY-MM-DDThh:mm:ss.mmmZ`, the line one taken at write time
  ([recorder.rs:927-933](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/rollout/src/recorder.rs#L927-L933),
  [2077-2082](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/rollout/src/recorder.rs#L2077-L2082));
  local values all had three fraction digits and `Z`. `task_*` `started_at`/`completed_at`: epoch
  seconds; `item_completed` `*_at_ms`: epoch ms; `create_time`: fractional epoch seconds;
  `history.jsonl` `ts`: epoch seconds.
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
  `chatgpt:<workspace uuid>:<user id>` ([section 10](#10-other-stores)).
- **Project.** `session_meta.payload.cwd`, updated per turn by
  `turn_context.payload.cwd`; `workspace_roots` lists extra roots.
- **Branch.** `session_meta.payload.git.branch`, set once at thread
  creation, absent outside a git repository.
- **Model.** `turn_context.payload.model`; `model_provider` on
  `session_meta`. No per-message model. Codex Desktop also appends
  `event_msg` `thread_settings_applied` (`model`, `reasoning_effort`
  and the permission fields) the moment the user changes a setting,
  before the next turn (macOS, build 26.1013.40934, 2026-10-18;
  [section 1](#1-source-and-evidence)); `state_5.sqlite` `threads.model` keeps
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
- **Joins.** Tool call to result: `call_id`, equal on the call and its
  `*_output`. Turn: `turn_id` on `turn_context`, `task_started`,
  `task_complete`, `item_completed` and in each item's metadata passthrough.
  An `item_completed` item that a code-mode `exec` call produced (the local
  `web.search`) has its own id, not the call's `call_id`, so nothing joins it
  to the call except its position between the call and its output (local).

### 10. Other stores

#### `history.jsonl`

Each line is `{session_id, ts, text}`, `ts` epoch **seconds**, `session_id` the thread id, one line
per prompt typed into the TUI
([message-history/src/lib.rs:61-66](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/message-history/src/lib.rs#L61-L66),
[127-138](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/message-history/src/lib.rs#L127-L138)).
Written unless `history.persistence = "none"`
([config/src/types.rs:211-219](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/config/src/types.rs#L211-L219));
trimmed oldest-first when `history.max_bytes` is set
([message-history/src/lib.rs:191-195](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/message-history/src/lib.rs#L191-L195)).
It can outlive the rollout it names (deleted or ephemeral threads), so it is the one place such a
prompt survives. Local: one line, those three keys, 10-digit `ts`.

#### `session_index.jsonl`

One `{id, thread_name, updated_at}` line is appended per rename, newest wins, `updated_at` RFC 3339
UTC with nanoseconds
([rollout/src/session_index.rs:24-48](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/rollout/src/session_index.rs#L24-L48)).
Titles only; local shape matches. Codex Desktop also lists the guardian review thread, as
`Guardian review`, and a scheduled task's thread, under the task's name (macOS, build 26.1013.40934,
2026-10-18; [section 1](#1-source-and-evidence)). The app's delete removes the thread's line.

#### `state_5.sqlite` threads

`state_5.sqlite` `threads`: `id`, `rollout_path`, `created_at`, `cwd`, `title`, `git_sha`,
`git_branch`, `git_origin_url` and later `first_user_message`, `preview`
([state/migrations/0001_threads.sql:1-19](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/state/migrations/0001_threads.sql#L1-L19),
[0007_threads_first_user_message.sql:1](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/state/migrations/0007_threads_first_user_message.sql#L1),
[0032_threads_preview.sql:1](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/state/migrations/0032_threads_preview.sql#L1));
`thread_spawn_edges` links parent and child threads
([0021_thread_spawn_edges.sql:1-5](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/state/migrations/0021_thread_spawn_edges.sql#L1-L5)).
A row whose rollout is gone still holds the first prompt. The file name is fixed beside the other
databases
([state/src/sqlite.rs:34-39](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/state/src/sqlite.rs#L34-L39)).
The columns the parser reads (issue 122), each only when the table has it:

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
- `first_user_message`: the first `UserMessage` event's text, trimmed and with the
  `## My request for Codex:` prefix removed, or `[Image]` or `[Audio]` for a prompt with no text
  ([state/src/extract.rs:184-196](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/state/src/extract.rs#L184-L196),
  [protocol/src/protocol.rs:145-150](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/protocol.rs#L145-L150),
  [2614-2635](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/protocol.rs#L2614-L2635)).
  No column records when the prompt was typed: `created_at` is the thread's creation, which the TUI
  does before the first prompt.

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

#### `thread_history_1.sqlite`

`thread_history_1.sqlite`: `thread_turns`, `thread_items` (`item_json`,
the app-server's camelCase `ThreadItem`), `thread_realtime_items`, keyed
by `rollout_ordinal`
([state/thread_history_migrations/0001_thread_history.sql:1-38](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/state/thread_history_migrations/0001_thread_history.sql#L1-L38)).
A projection of paginated rollouts; local item types were `userMessage`,
`webSearch`, `agentMessage`, the same three items as the rollout's
`item_completed` lines. Nothing found that is not in the rollout.
Codex Desktop on Windows (observed 2026-10-15,
[section 1](#1-source-and-evidence)) added `reasoning`, `commandExecution` and
`fileChange` items, also all in its rollouts. Record shapes from source
(issue 122):

- What is projected: one rollout line at a time, `task_started`,
  `task_complete` and `turn_aborted` into `thread_turns` and each
  `item_completed` into `thread_items`; every other line type
  projects nothing
  ([app-server-protocol/src/protocol/thread_history_projection.rs:21-99](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/app-server-protocol/src/protocol/thread_history_projection.rs#L21-L99)).
  `history_mode` `legacy` rollouts are not projected
  ([line 1-4](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/app-server-protocol/src/protocol/thread_history_projection.rs#L1-L4)).
- `thread_turns`: `status` `inProgress`, `completed`, `interrupted` or `failed`, `started_at` and
  `completed_at` in epoch seconds (the turn events' fields;
  [protocol/src/protocol.rs:2189-2192](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/protocol.rs#L2189-L2192)),
  `duration_ms`, `error_json`; `rollout_end_ordinal` from migration 0003
  ([0003_turn_rollout_positions.sql:1-3](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/state/thread_history_migrations/0003_turn_rollout_positions.sql#L1-L3);
  written at
  [thread-store/src/local/thread_history.rs:316-351](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/thread-store/src/local/thread_history.rs#L316-L351)).
  The two events are the rollout's `task_started` and `task_complete` lines
  ([protocol/src/protocol.rs:1407-1418](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/protocol.rs#L1407-L1418)).
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
  `userMessage` (`content[]` of `UserInput`, `text` inputs with `text`;
  [v2/turn.rs:425-459](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/app-server-protocol/src/protocol/v2/turn.rs#L425-L459)),
  `agentMessage` (`text`, the content blocks concatenated, `phase`), `reasoning` (`summary[]`,
  `content[]`, strings), `commandExecution` (`command` a display string, `cwd`, `status`,
  `aggregatedOutput`, `exitCode`, `durationMs`), `fileChange` (`changes[]` of `path`, `kind`,
  `diff`;
  [v2/item.rs:1137-1144](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/app-server-protocol/src/protocol/v2/item.rs#L1137-L1144)),
  `mcpToolCall` (`server`, `tool`, `arguments`, `result`, `error`), `dynamicToolCall` (`tool`,
  `arguments`, `contentItems`), `functionCallOutput`, `plan` (`text`), `subAgentActivity`,
  `webSearch` (`id`, `query`, `action`, `results`;
  [ext/items/src/web_search.rs:11-22](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/ext/items/src/web_search.rs#L11-L22)),
  `imageGeneration` (`revisedPrompt`, `status`, `savedPath`, and the image itself in `result`),
  `sleep` (`durationMs`), `hookPrompt`, `collabAgentToolCall`, `imageView`, `enteredReviewMode`,
  `exitedReviewMode`, `contextCompaction`.

The two files join the rollout on the thread id, which is the rollout
rows' `session_id`; the projection has no `cwd`, so its project path is
taken from the `threads` row of the same thread. What it survives is
what `state_5.sqlite` survives; it never holds a legacy rollout's
thread.

#### `logs_2.sqlite`

`logs_2.sqlite` `logs`: Codex's own tracing log, one row per log
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
([section 13](#13-parser-plan)); a body field may
come in any order, and the first logs migration named the body column
`message`. Not seen on a real install: the feedback row is read from
a synthetic fixture only.

Codex Desktop writes the per-call permission decisions here and
nowhere else (macOS, build 26.1013.40934, 2026-10-18;
[section 1](#1-source-and-evidence)); `ts` was integer epoch seconds:

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

#### `state_5.sqlite` remote control enrollments

`state_5.sqlite` `remote_control_enrollments`: one row per remote
control enrollment, the link that lets a ChatGPT client drive this
host's app server (`codex remote-control`; `websocket_url`,
`account_id`, `app_server_client_name`, `server_id`, `environment_id`,
`server_name`, `updated_at`, and `remote_control_enabled` from
migration 0037;
[state/migrations/0024_remote_control_enrollments.sql:1-10](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/state/migrations/0024_remote_control_enrollments.sql#L1-L10),
[0037_remote_control_enrollments_enabled.sql:1-2](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/state/migrations/0037_remote_control_enrollments_enabled.sql#L1-L2)).
It names the host's enrollment, not a thread. Empty on the Windows
install of [section 1](#1-source-and-evidence). On macOS (build 26.1013.40934,
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
([section 13](#13-parser-plan)).

#### `sqlite/codex-dev.db`

`sqlite/codex-dev.db`: written only by the ChatGPT desktop app (observed
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
of [section 1](#1-source-and-evidence) it held five rows: three `vscode`, and two
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
Codex source (the app's code is not in the repository; see
[Sync, relay and origin](#sync-relay-and-origin-rows)).
`codex_schema_migrations` rows carry the app version (`app_version`
`26.1007.71326`, `build_flavor` `prod`). The chat's text is not in it.
The `codex-cli` parser does not read it: the automation is read from
`automation.toml`, and a run would be in `automation_runs`, which no
real install has shown filled. The `chatgpt-desktop` parser reads its
`chatgpt` rows, the account's ChatGPT conversations, since analyzer
0.17.0 ([`chatgpt-desktop.md`](chatgpt-desktop.md)). On macOS (build 26.1013.40934,
2026-10-18; [section 1](#1-source-and-evidence)) the database also had
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

#### Automations

`automations/<slug>/automation.toml`: one directory per automation of
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
[section 1](#1-source-and-evidence)) the file was 356 bytes with the same keys,
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

#### Ambient suggestions

`ambient-suggestions/<40 hex>/ambient-suggestions.json`: the desktop
app's suggestions for a project (observed on Windows, 2026-10-15,
139 bytes): `currentSuggestionIds` (empty list), `generatedAtMs` number,
`projectRoot` absolute path, `suggestions` (empty list). Governed by
`desktop.ambient-suggestions-enabled` in `config.toml`. Not read; a
file holding suggestions has not been observed.

#### `.codex-global-state.json`

`.codex-global-state.json` (and its `.bak`): the ChatGPT desktop
app's state, one JSON object (macOS, build 26.1013.40934, 2026-10-18
and 2026-10-19, [section 1](#1-source-and-evidence); not in the Codex source this
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
secondary source ([section 13](#13-parser-plan)).

#### Thread locks and shell snapshots

`thread-writer-locks/` (`.coordination.lock` and one
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
([section 3](#3-credentials)).
The parser reads neither.

#### Standing grants

From the source review of 2026-10-19, at
[`4e7b9e2`](https://github.com/openai/codex/commit/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857).
The parser reads none of these.

- `rules/default.rules`: when the user answers an approval prompt
  with "approve and remember" (`ReviewDecision::ApprovedExecpolicyAmendment`,
  [protocol/src/protocol.rs:4269-4304](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/protocol/src/protocol.rs#L4269-L4304)),
  Codex appends one Starlark line (Starlark is the Python-like
  configuration language the exec policy is written in)
  `prefix_rule(pattern=["<token>", ...], decision="allow")` to
  `<CODEX_HOME>/rules/default.rules`
  ([core/src/session/handlers.rs:181-193](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/core/src/session/handlers.rs#L181-L193),
  [core/src/exec_policy.rs:466-490](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/core/src/exec_policy.rs#L466-L490),
  [874-876](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/core/src/exec_policy.rs#L874-L876),
  [execpolicy/src/amend.rs:65-80](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/execpolicy/src/amend.rs#L65-L80)),
  and a network allow or deny answer appends
  `network_rule(host=..., protocol=..., decision="allow"|"deny",
  justification=...)`
  ([amend.rs:85-124](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/execpolicy/src/amend.rs#L85-L124)).
  A line carries no time and no thread; the file's modification time
  is the last grant. Every other `*.rules` file under `rules/` is
  loaded too
  ([exec_policy.rs:681](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/core/src/exec_policy.rs#L681)).
- `config.toml`: the standing policy keys `approval_policy`,
  `approvals_reviewer`, `sandbox_mode` and `default_permissions`
  ([config/src/config_toml.rs:195](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/config/src/config_toml.rs#L195),
  [200](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/config/src/config_toml.rs#L200),
  [224](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/config/src/config_toml.rs#L224),
  [239](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/config/src/config_toml.rs#L239));
  `[projects."<path>"] trust_level`, `trusted` or `untrusted`
  ([config/src/config_toml.rs:473](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/config/src/config_toml.rs#L473),
  [core/src/config/mod.rs:2464](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/core/src/config/mod.rs#L2464),
  [protocol/src/config_types.rs:642-645](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/protocol/src/config_types.rs#L642-L645));
  and, for an MCP tool call the user approved for good
  (`ApprovedMcpPolicyAmendment`), `approval_mode = "approve"` under
  `mcp_servers.<server>.tools.<tool>`,
  `plugins.<plugin>.mcp_servers.<server>.tools.<tool>` or, for a
  ChatGPT app connector, `apps.<connector>.tools.<tool>`
  ([core/src/mcp_tool_call.rs:2394-2411](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/core/src/mcp_tool_call.rs#L2394-L2411),
  [2428-2457](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/core/src/mcp_tool_call.rs#L2428-L2457),
  [2472-2490](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/core/src/mcp_tool_call.rs#L2472-L2490)).
  "Approve for this session" (`ApprovedForSession`) is kept in memory
  only and leaves no file.
- `state_5.sqlite` `guardian_review_feedback` (`id`, `thread_id`,
  `record` BLOB; migration 0060, not at
  [`3e23877`](https://github.com/openai/codex/commit/3e238776e857eccd3bde6bff3026e2e9798f6524),
  [state/migrations/0060_guardian_review_feedback.sql:1-5](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/state/migrations/0060_guardian_review_feedback.sql#L1-L5)):
  one row per automatic review (the desktop app's Approve for me
  reviewer) that did not allow the action: `record` is a JSON object
  `reviewed_thread_id`, `reviewed_turn_id`, `target_item_id`,
  `reviewer_thread_id`, `model`, `status` (`denied`,
  `invalid_decision`, `missing_decision`, `failed`, `timed_out`,
  `aborted`), `decision` (the reviewer's verdict text), `action` (the
  reviewed command or patch), `instructions`, `history` (the
  reviewer's own response items) and `context_omitted`
  ([ext/guardian-reviewer/src/feedback.rs:17-30](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/ext/guardian-reviewer/src/feedback.rs#L17-L30),
  [57-85](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/ext/guardian-reviewer/src/feedback.rs#L57-L85),
  [core/src/guardian/feedback.rs:6-44](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/core/src/guardian/feedback.rs#L6-L44),
  [state/src/runtime/guardian_feedback.rs:33-50](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/state/src/runtime/guardian_feedback.rs#L33-L50)).
  An allowed review writes no row, and nothing is written when
  feedback is turned off or the thread is ephemeral. The row outlives
  the reviewer thread; its `thread_id` references `threads(id)` with
  `ON DELETE CASCADE`, so it is meant to go with the reviewed thread. The table was present on
  the macOS install of 2026-10-18
  ([section 1 of the collector
  document](#1-source-and-evidence)).
- Log lines of answers the parser does not read: beside
  `op=ExecApproval`, the core's `Submission` debug line
  ([core/src/session/handlers.rs:487-495](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/core/src/session/handlers.rs#L487-L495))
  prints `PatchApproval { id, decision }` for an `apply_patch`
  approval and `RequestPermissionsResponse { id, scope,
  strict_auto_review }` for a permissions request
  ([protocol/src/protocol.rs:769-776](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/protocol/src/protocol.rs#L769-L776),
  [803](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/protocol/src/protocol.rs#L803)).

#### Other past-use stores

From the source review of 2026-10-19, at
[`4e7b9e2`](https://github.com/openai/codex/commit/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857).
Each is secondary, derived from rollouts; the parser reads none.

- Memories, when the `memories` feature is on (off by default,
  [features/src/lib.rs:1303-1305](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/features/src/lib.rs#L1303-L1305)):
  `memories_1.sqlite` (and `memories_v2_1.sqlite`) `stage1_outputs`,
  one row per thread with `thread_id`, `raw_memory`,
  `rollout_summary`, `rollout_slug` and `source_updated_at`
  ([state/memory_migrations/0001_memories.sql:1-12](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/state/memory_migrations/0001_memories.sql#L1-L12),
  [state/src/sqlite.rs:114-119](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/state/src/sqlite.rs#L114-L119)),
  and the consolidated files under `memories/`:
  `rollout_summaries/<stem>.md`, each headed `thread_id:`,
  `updated_at:`, `rollout_path:`, `cwd:` and `git_branch:` lines
  before a model-written summary of the thread, `raw_memories.md`
  with the same header per thread, `MEMORY.md` and
  `memory_summary.md`
  ([memories/write/src/lib.rs:39-40](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/memories/write/src/lib.rs#L39-L40),
  [storage.rs:110-136](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/memories/write/src/storage.rs#L110-L136),
  [workspace.rs:87](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/memories/write/src/workspace.rs#L87),
  [101](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/memories/write/src/workspace.rs#L101)).
  A thread delete removes its `stage1_outputs` row
  ([state/src/runtime/memory_versions.rs:39-51](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/state/src/runtime/memory_versions.rs#L39-L51)),
  and its summary file goes only when the next consolidation prunes
  the files it no longer keeps
  ([storage.rs:80-108](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/memories/write/src/storage.rs#L80-L108)),
  so until then the summary names a thread whose rollout is gone.
  Joins on `thread_id`, `cwd` and `rollout_path`.
- Thread goals: `goals_1.sqlite` `thread_goals` (`thread_id`,
  `objective`, `status`, `token_budget`, `created_at_ms`,
  `updated_at_ms`;
  [state/goals_migrations/0001_thread_goals.sql:1-17](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/state/goals_migrations/0001_thread_goals.sql#L1-L17)),
  the objective the user set for a thread, also persisted in the
  rollout as `event_msg` `thread_goal_updated` (`thread_id`,
  `turn_id`, `goal.objective`, `goal.status`;
  [rollout/src/policy.rs:131-139](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/rollout/src/policy.rs#L131-L139),
  [protocol/src/protocol.rs:4235-4257](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/protocol/src/protocol.rs#L4235-L4257)),
  which the parser skips with the other unlisted events. Removed with
  the thread.
- `db-backups/sqlite-<timestamp>-<n>/`: a database Codex found
  corrupt, renamed aside with its sidecars before a fresh one is
  built
  ([state/src/runtime/recovery.rs:16](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/state/src/runtime/recovery.rs#L16),
  [181-200](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/state/src/runtime/recovery.rs#L181-L200),
  [241-250](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/state/src/runtime/recovery.rs#L241-L250)).
  A backed-up `state_5.sqlite` keeps the `threads` rows of its time,
  deleted threads included; the parser wants only
  `.codex/state_5.sqlite` itself.

### 11. Format versions

- **History mode.** `session_meta.history_mode` (`legacy` default, `paginated`;
  [protocol.rs:775-782](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/protocol.rs#L775-L782)).
  The app server starts non-ephemeral threads paginated when the store supports it
  ([app-server/src/request_processors/thread_processor.rs:1462-1465](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/app-server/src/request_processors/thread_processor.rs#L1462-L1465));
  the local TUI thread was paginated. Paginated files add `ordinal` and `item_completed` items and
  drop the legacy `user_message`/`agent_message` events. A background legacy-to-paginated rewrite
  exists behind `background_paginated_rollout_migration`, off by default
  ([features/src/lib.rs:1224-1229](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/features/src/lib.rs#L1224-L1229),
  [thread-store/src/local/rollout_migration.rs:1-9](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/thread-store/src/local/rollout_migration.rs#L1-L9)).
- **Compression and archive.** `.jsonl.zst` and `archived_sessions/`
  ([section 7](#7-transcript-stores)); Codex materialises a compressed file back to `.jsonl` before
  appending to it
  ([compression.rs:104-105](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/rollout/src/compression.rs#L104-L105)),
  so either form may be present.
- **Flat layout.** Older releases wrote `sessions/rollout-<time>-<uuid>.jsonl` without date
  directories (the example in
  [recorder.rs:82](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/rollout/src/recorder.rs#L82));
  the current lister walks only `YYYY/MM/DD`
  ([list.rs:900-920](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/rollout/src/list.rs#L900-L920)).
- **Standalone CLI and desktop app on one host.** On Windows the
  standalone CLI (installed by OpenAI's PowerShell installer under
  `.codex/packages/standalone`) and Codex Desktop inside the ChatGPT app
  write the same `.codex` tree, sessions and login (observed
  2026-10-15, CLI 0.162.1, desktop 0.162.0-alpha.17.2). Their rollouts
  have the same envelope and `session_meta` keys and differ in
  `originator` and `cli_version` ([section 9](#9-joins-and-timestamps));
  only the CLI wrote `history.jsonl`. The parser reads both alike.
- **Renames kept for compatibility.** `session_meta` without `session_id`,
  `agent_type` for `agent_role`, `turn_started`/`turn_complete` aliases,
  `compaction_summary` for `compaction`; `TurnContextItem.summary` is
  written only for older readers.
- **Not determined at this commit:** whether pre-envelope rollouts (no
  `type`/`payload` wrapper) exist on disk from very early releases; the
  current reader rejects lines without `timestamp`.

- **Drift from
  [`3e23877`](https://github.com/openai/codex/commit/3e238776e857eccd3bde6bff3026e2e9798f6524) to
  [`4e7b9e2`](https://github.com/openai/codex/commit/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857)
  (source review of 2026-10-19).** Unchanged: the line envelope and `RolloutItem` set
  ([history/src/lib.rs:215-231](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/history/src/lib.rs#L215-L231)),
  `SessionMeta`
  ([protocol/src/protocol.rs:3256-3331](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/protocol/src/protocol.rs#L3256-L3331)),
  the `ResponseItem` variants, the database file names
  ([state/src/sqlite.rs:41-46](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/state/src/sqlite.rs#L41-L46)),
  `sessions/` and `archived_sessions/`
  ([rollout/src/lib.rs:86-87](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/rollout/src/lib.rs#L86-L87))
  and the `/feedback` marker message
  ([feedback/src/lib.rs:755](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/feedback/src/lib.rs#L755)).
  Changed:
  - `TurnContextItem` dropped `network` (the allowed and denied domain
    lists), `workspace_roots`, `current_date`, `timezone`,
    `personality` and `multi_agent_mode` (present at
    [protocol.rs:3314-3346 at `3e23877`](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/protocol/src/protocol.rs#L3314-L3346))
    and gained `root_turn_id`, `disabled_plugin_ids`,
    `file_system_sandbox_policy`, `comp_hash`, `realtime_active` and
    `cyber_access_program`; `summary` is optional
    ([protocol.rs:3428-3468](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/protocol/src/protocol.rs#L3428-L3468)).
    The parser's `permission mode:` row prints `network=-` for a
    rollout of this version.
  - `task_started` gained `turn_attribution` (`turn_id`,
    `turn_trigger`, `parent_turn_id`, `initiating_agent_path`,
    `root_turn_id`) and `root_turn_id`
    ([protocol.rs:2302-2325](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/protocol/src/protocol.rs#L2302-L2325),
    [protocol/src/turn_input.rs:80-86](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/protocol/src/turn_input.rs#L80-L86)):
    the field the desktop app's 0.163.0-alpha rollouts already carried
    and the parser reads.
  - The `op=ExecApproval` debug line now has its own format,
    `ExecApproval { id, turn_id, decision: <word> }`, the word one of
    `approved`, `approved_with_amendment`, `approved_for_session`,
    `approved_mcp_policy_amendment`,
    `approved_with_network_policy_allow`,
    `denied_with_network_policy_deny`, `denied`, `timed_out`, `abort`
    ([protocol.rs:759-767](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/protocol/src/protocol.rs#L759-L767),
    [4323-4339](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/protocol/src/protocol.rs#L4323-L4339)),
    where the derived format printed the enum (`Denied { rejection:
    ... }`). The parser's pattern takes the first word either way.
  - `event_msg` `elicitation_abandoned` is new and transient
    ([rollout/src/policy.rs:199](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/rollout/src/policy.rs#L199)).
  - New tables: `guardian_review_feedback` ([section 10](#10-other-stores)),
    `thread_read_receipts`
    ([state/migrations/0061_thread_read_state.sql:1-8](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/state/migrations/0061_thread_read_state.sql#L1-L8)),
    and `thread_turns.root_turn_id`
    ([state/thread_history_migrations/0008_thread_turn_root.sql:1](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/state/thread_history_migrations/0008_thread_turn_root.sql#L1)).
    No column the parser selects was removed.

### 12. Secrets

The credential files under `~/.codex` (`auth.json`, `.credentials.json`, `secrets/`,
`.sandbox-secrets/`) are listed in [section 3](#3-credentials). Inside
the stores this document describes:

- `session_meta.payload.creator_account_id` and `creator_user_id`, and the `state_5.sqlite`
  `threads` columns of the same names, name the ChatGPT account and user
  ([section 9](#9-joins-and-timestamps)); `token_count.rate_limits` names the account's plan
  ([Observed](#observed)).
- `.codex-global-state.json` holds the user's prompts, the account id inside key names and, per
  [section 3](#3-credentials), the ChatGPT conversation resume tokens; the collector flags it
  `secret: true` ([`.codex-global-state.json`](#codex-global-statejson)).
- `shell_snapshots/<thread id>.<unix ns>.sh` replays the user's exported login-shell environment, so
  an API key exported there is copied into it; collector 1.15.0 flags the files ([Thread locks and
  shell snapshots](#thread-locks-and-shell-snapshots)).
- `state_5.sqlite` `remote_control_enrollments` holds no token, and where remote control's server
  token is stored was not found ([`state_5.sqlite` remote control
  enrollments](#state_5sqlite-remote-control-enrollments)).

### 13. Parser plan

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
| `event_msg` `task_started`, `task_complete` | `system`; `task_started turn=<id>` as before (so the `thread_history_1.sqlite` copy still pairs with it), followed by `turn trigger: <turn_trigger> turn=<id>` when `turn_attribution.turn_trigger` is set (values seen in [section 1](#1-source-and-evidence): `composer`, `remote_ios`, `remote_android`, `guardian_review`, `scheduled_task_setup`, `automation_heartbeat_run_now`, `automation_heartbeat_scheduled`; a `remote_*` turn came from a paired phone) |
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
| `thread_history_1.sqlite` `thread_items` row (secondary) | `userMessage` `user`, `agentMessage` `assistant`, `reasoning` `thinking` (opt-in), at `completed_at_ms`; `hookPrompt`, `contextCompaction` none; any other item renamed to the turn-item form and rendered as the `item_completed` rows above, at `started_at_ms` and `completed_at_ms` (else `created_at_ms`); an `item_json` that does not decode to a JSON object is one `system` row per record at the end of the file's rows, `parser: unparseable record <rowid> (<reason>): <item_json as stored>`, `source_line` the rowid, `session_id` and `project_path` the record's thread's (issue 184) |
| `automations/<slug>/automation.toml` (Codex only) | one `system` row `scheduled task: <id> name=<name> kind=<kind> status=<status> rrule=<rrule> target_thread=<target_thread_id> created=<created_at> updated=<updated_at> (from <file>, file mtime) prompt: <prompt>` at the file's modification time, `session_id` the target thread; an unreadable file is one `system` row (issue 119) |
| `logs_2.sqlite` `logs` row `codex_core::session::handlers` `op=ExecApproval` or `codex_app_server::outgoing_message` `CommandExecutionRequestApproval` (Codex Desktop) | `system` `permission decision: <decision> exec <item id> turn=<turn id> (from logs_<N>.sqlite logs, ts)` at `ts` from the handlers row (`denied`, `approved` seen), `session_id` the row's thread id, `tool_use_id` the governed item's id (`exec-<uuid>`, [section 10](#10-other-stores)); a response row (`Decline`, `Accept`) with no handlers row within two seconds is `permission decision: <decision> request <n> (from logs_<N>.sqlite logs, ts)` with no session (issue 160) |
| `state_5.sqlite` `remote_control_enrollments` row | `system` `remote control: enabled=<0\|1> server=<server_id> environment=<environment_id> host=<server_name> client=<app_server_client_name> account=<account_id>` at `updated_at`, `session_id` empty (issue 160) |
| `.codex-global-state.json` (secondary, Codex Desktop) | `user` for each `prompt-history` entry of a thread, with an empty `timestamp_utc` (matched on text and session), `session_id` the thread id; `system` `session deleted: <id>` for each `codex-writing-block-deleted-thread-v1:<id>` key and `system` `permission mode (standing): ...` for each `heartbeat-thread-permissions-by-id` entry, at the file's modification time; `system` `thread description: ...` for each `thread-descriptions-v1` entry; one `system` `remote control: mobile device connected=<bool> environment=<id>` row from the two top-level keys; one `system` `scratch directory: <path> (projectless thread <id>) (from <file> thread-projectless-output-directories, file mtime)` row for each `thread-projectless-output-directories` entry, `session_id` the thread id and `project_path` the path itself, so inventory.json lists the directory under `scratch_directories` (issue 149); a file that does not decode is one `parser:` row (issue 160) |

#### Permission rows

Permission state is the per-turn `turn_context` policy above and, on Codex Desktop, every
`thread_settings_applied` event and the standing per-thread entries of `.codex-global-state.json`.
The rollout holds no per-call decision: approval requests and their answers are transient events
that the rollout never stores
([policy.rs:160-223](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/rollout/src/policy.rs#L160-L223)),
so a rollout shows what the policy allowed, not what the user approved. Codex Desktop logs the
user's answers in `logs_2.sqlite` and records an automatic answer as the verdict of a guardian
review thread (macOS, build 26.1013.40934, 2026-10-18; [section 10](#10-other-stores)); the parser
yields a `permission decision:` row from each, joined to the governed call on its item id. The
approval dialog of that build offered no standing "always allow" grant for a command.

From the source review of 2026-10-19: the standing grants in `rules/default.rules` and
`config.toml`, the `guardian_review_feedback` records and the `PatchApproval` and
`RequestPermissionsResponse` log lines are on disk and not read
([Standing grants](#standing-grants)). A plan for them: one
`permission setting: <rule> (from .codex/rules/default.rules, file mtime)` row per rule line, one
`permission setting:` row per standing key, project trust entry and tool `approval_mode` in
`config.toml`, and one `permission decision: <status> (auto_review) ...` row per
`guardian_review_feedback` record, joined to the governed call on `target_item_id`; the
`PatchApproval` line joins on its id like `ExecApproval`.

#### Model rows

The model is recorded per turn, in `turn_context.model`, and on Codex Desktop also at each change,
in `thread_settings_applied`; there is no per-message model, so the model rows follow the turns and
the settings events.

#### Past-use rows and secondary sources

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

From the source review of 2026-10-19: memories (secondary: `rollout_summaries/*.md`,
`raw_memories.md`, `stage1_outputs`), thread goals (primary, in the rollout's `thread_goal_updated`
events; `thread_goals` secondary) and `db-backups/` copies of `state_5.sqlite` (secondary) are not
read ([Other past-use stores](#other-past-use-stores)).

#### Sync, relay and origin rows

Codex has no session sync. The thread store is local only: the two backends are `Local` (rollouts
and SQLite) and `InMemory`
([core/src/config/mod.rs:599-607](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/core/src/config/mod.rs#L599-L607)),
and the old `experimental_thread_store_endpoint` for a remote store is now refused at load
([3251-3254](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/core/src/config/mod.rs#L3251-L3254)).
The thread metadata sync of [section 9](#9-joins-and-timestamps) copies rollout facts into
`state_5.sqlite` and calls no server
([thread-store/src/thread_metadata_sync.rs:34-38](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/thread-store/src/thread_metadata_sync.rs#L34-L38)).
`codex resume` reopens a local rollout
([cli/src/main.rs:206-207](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/cli/src/main.rs#L206-L207)),
and the app server's `thread/*` methods have no share or upload method. What does leave the host,
beyond the model API call:

- **`/feedback`** ("send logs to maintainers";
  [tui/src/slash_command.rs:73](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/tui/src/slash_command.rs#L73),
  [93](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/tui/src/slash_command.rs#L93))
  sends a report to OpenAI's Sentry project
  ([feedback/src/lib.rs:60-61](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/feedback/src/lib.rs#L60-L61)).
  The TUI asks "Upload logs?" and lists the files
  ([tui/src/bottom_pane/feedback_view.rs:252](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/tui/src/bottom_pane/feedback_view.rs#L252),
  [282-285](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/tui/src/bottom_pane/feedback_view.rs#L282-L285));
  on yes the open thread's rollout
  ([tui/src/app/background_requests.rs:623-627](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/tui/src/app/background_requests.rs#L623-L627))
  and the rollouts of its subagent threads are attached
  ([app-server/src/request_processors/feedback_processor.rs:179-196](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/app-server/src/request_processors/feedback_processor.rs#L179-L196)),
  packed into `rollouts.tar.gz` in a system temporary directory
  ([feedback/src/lib.rs:840-853](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/feedback/src/lib.rs#L840-L853)).
  On no, the report carries the category, the note and tags only, and the TUI says "Feedback
  recorded (no logs)"
  ([feedback_view.rs:54-58](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/tui/src/bottom_pane/feedback_view.rs#L54-L58)).
  Opt-in per report; the whole flow is on by default and turned off by `[feedback] enabled = false`
  in `config.toml`
  ([config/src/types.rs:233-236](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/config/src/types.rs#L233-L236),
  [core/src/config/mod.rs:4498-4502](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/core/src/config/mod.rs#L4498-L4502),
  [feedback_processor.rs:62-66](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/app-server/src/request_processors/feedback_processor.rs#L62-L66)).
  The marker is the `logs_2.sqlite` row of [section 10](#10-other-stores). The parser yields one
  `system` row per such log row (`target` `codex_feedback` and the message
  `feedback event uploaded to Sentry`; the other `codex_feedback` rows report attachment failures
  and are not uploads),
  `session synced: feedback report uploaded to Sentry, attachments <uploaded_attachments> failed <attachments_failed> (from logs_2.sqlite logs, ts)`,
  `-` for a field the body lacks, at `ts` plus `ts_nanos`, with `session_id` the body's `thread_id`
  (empty for a `no-active-thread-` id) and the project and branch of that thread's `threads` row;
  the parser sets `records_sync`, so a thread without the row is `synced` `no` in `sessions.jsonl`.
  A report with 0 attachments sent no rollout. Fixture only: no real install has shown the row. The
  row survives the rollout's loss outside Codex for up to 10 days; Codex's own thread delete removes
  it with the thread, Codex offers no delete of the Sentry copy, and nothing local records one.
- **`codex cloud`** (experimental;
  [cli/src/main.rs:227-229](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/cli/src/main.rs#L227-L229))
  creates a Codex Cloud task, a run on OpenAI's servers against a GitHub branch: the typed prompt,
  the environment id and the branch, plus a local diff only when `CODEX_STARTING_DIFF` is set
  ([cloud-tasks-client/src/http.rs:332-372](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/cloud-tasks-client/src/http.rs#L332-L372)).
  It sends no local thread; the task's transcript is server-side, and `codex apply` fetches a task's
  diff back
  ([chatgpt/src/get_task.rs:37-38](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/chatgpt/src/get_task.rs#L37-L38)).
  Its only local trace is an `error.log` that it appends to in the directory it was started from,
  not under `~/.codex`
  ([cloud-tasks/src/util.rs:18-28](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/cloud-tasks/src/util.rs#L18-L28),
  [cloud-tasks-client/src/http.rs:911-920](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/cloud-tasks-client/src/http.rs#L911-L920)),
  with lines `[<RFC 3339 time>] new_task: created id=<task id> env=<env id> prompt_chars=<n>`
  ([http.rs:374-381](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/cloud-tasks-client/src/http.rs#L374-L381)),
  the GitHub origins it matched
  ([cloud-tasks/src/env_detect.rs:51](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/cloud-tasks/src/env_detect.rs#L51))
  and the `account_id` it authenticated as
  ([cloud-tasks/src/lib.rs:103](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/cloud-tasks/src/lib.rs#L103)).
  No catalog line collects that file; no row is proposed until it is.
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
  26.1013.40934, 2026-10-18 and 2026-10-19, [section 1](#1-source-and-evidence)),
  it leaves two records: the host-level `remote_control_enrollments`
  row of [section 10](#10-other-stores), which the parser yields as a
  `remote control:` row, and a per-turn mark, `turn_attribution.turn_trigger`
  `remote_ios` or `remote_android` on a turn sent from a paired phone,
  which the parser's `turn trigger:` row carries; the
  phone's own connection is in `logs_2.sqlite`. The vendor page
  [Remote connections | ChatGPT Learn](https://learn.chatgpt.com/docs/remote-connections)
  (read 2026-10-18) says "Repository files and local documents come
  from the connected host". The relay carries control, not a copy of
  the thread, so the parser marks no session synced or relayed for it.
- **`--remote <ADDR>`** points the TUI at an app server the user runs elsewhere
  ([cli/src/main.rs:962-974](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/cli/src/main.rs#L962-L974)).
  The rollout is written on that server's host, but the TUI still appends each prompt to the local
  `history.jsonl`
  ([tui/src/app/thread_routing.rs:557-566](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/tui/src/app/thread_routing.rs#L557-L566)),
  so a `history.jsonl` session with no local rollout may be such a thread. Not a vendor upload.
- **Analytics** go to `<chatgpt base URL>/codex/analytics-events/events`
  ([analytics/src/client.rs:154](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/analytics/src/client.rs#L154))
  as events keyed by thread id
  ([analytics/src/events.rs:257](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/analytics/src/events.rs#L257));
  no prompt or reply text field was found (searched `prompt`, `text`, `user_message` in
  `analytics/src`). Turned off by `[analytics] enabled = false`
  ([config/src/types.rs:223-228](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/config/src/types.rs#L223-L228)).
  OpenTelemetry export, which can carry prompts and replies, is off by default and goes only to an
  exporter the user configures
  ([config/src/types.rs:597-611](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/config/src/types.rs#L597-L611),
  [647-657](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/config/src/types.rs#L647-L657)).
  Image attachments are kept inline in the rollout; the one attachment store uploads nothing
  ([attachment-store/src/lib.rs:160-170](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/attachment-store/src/lib.rs#L160-L170)).

The ChatGPT desktop app's own sync state is outside this source: its
client code is not in the repository (searched
`chatgpt-conversation-resume-tokens`, `resume-tokens`,
`conversation_origin`, `chatgpt_async_status`, `codex-dev.db`,
`local_thread_catalog` and `electron-persisted-atom-state` across the
clone; the only matches are unrelated token-usage replay code). The
`chatgpt` rows of `codex-dev.db` `local_thread_catalog` and the
resume tokens in `.codex-global-state.json`
([section 3](#3-credentials)) are
the app's index of ChatGPT conversations that live on the server; what
`chatgpt_async_status` and `conversation_origin` `tpp` mean, and
whether a local Codex thread is ever uploaded as a ChatGPT
conversation, was not determined from source. The macOS round of
2026-10-18 ([section 1](#1-source-and-evidence), build 26.1013.40934) answered the
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
([section 10](#10-other-stores)); with no remote copy, the delete dialog
offered none to remove. What `chatgpt_async_status` and
`conversation_origin` `tpp` mean is still not determined.

From the source review of 2026-10-19: covered; Codex records no relay and no
remote-origin session.

#### Scratch directory rows

Codex Desktop's projectless output directory is a scratch directory: the parser yields a
`scratch directory:` row for each `thread-projectless-output-directories` entry of
`.codex-global-state.json` (the table above), so inventory.json lists the directory under
`scratch_directories` (issue 149).

From the source review of 2026-10-19: a rollout `cwd` under `<home>/.codex/worktrees` is classed by
the catalog rule; one under a configured `git-worktree-root` is not, and no row marks it. The
worktree's `codex-thread.json` (`version`, `ownerThreadId`) sits in the source repository's git
directory for that worktree
([worktree/src/metadata.rs:19-27](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/worktree/src/metadata.rs#L19-L27),
[88-91](https://github.com/openai/codex/blob/4e7b9e285ba4ac6ce18ca452cf9e88d3d75ec857/codex-rs/worktree/src/metadata.rs#L88-L91)),
outside every catalog path.

#### Deletion rows

The desktop app's deletion marker already gives a `session deleted:` row. A delete through
`thread/delete` (the TUI, the app server) leaves no marker; what it removes and what survives it is
in [Deletion](#deletion)
and in [What survives a delete](#what-survives-a-delete), and the survivors that matter here are
`history.jsonl`, which the parser reads, and the memories files and `db-backups/`, which it does
not.

#### Bad-line rows

A bad line in a rollout or in `history.jsonl`, a cut or corrupt zstd frame, and a
`thread_history_1.sqlite` row whose `item_json` does not decode each give the rows in the table
above.

From the source review of 2026-10-19: a `thread_history_1.sqlite` row with an unreadable `item_json`
was one summary row (`parser: <n> thread_items row(s) with unreadable item_json, first at rowid
<n>`); it is now one row per record with the value in full, as the table above gives (issue 184;
fixture only, no real install has shown a corrupt row).

#### Fixtures

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

Sample rollout, paginated shape, at
`.codex/sessions/2026/10/02/rollout-2026-10-02T11-00-00-0199b2c3-1111-7aaa-8bbb-000000000001.jsonl`:

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

#### Injected user-role context

Rollouts without content kinds are classified per content block by the wrappers Codex itself
recognises as injected user-role context
([core/src/context/contextual_user_message.rs:22-37](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/core/src/context/contextual_user_message.rs#L22-L37)).
As in Codex's own check, the block must begin with the open marker after leading whitespace and end
with the close marker, ignoring ASCII case
([context-fragments/src/fragment.rs:116-130](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/context-fragments/src/fragment.rs#L116-L130)),
so a tag a person types inside a prompt leaves it `user`:

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

#### Subagent input and copied forks

Later `role: "user"` messages in a subagent's rollout stay `user`: the parent's v1 `send_input` tool
submits plain user input to the child
([core/src/agent/control.rs:134-143](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/core/src/agent/control.rs#L134-L143)),
and a person can also type into a subagent thread, because the TUI's `/subagents` picker makes it
the active thread and composer input is sent to the active thread
([tui/src/multi_agents.rs:1-5](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/tui/src/multi_agents.rs#L1-L5),
[tui/src/app/thread_routing.rs:475-497](https://github.com/openai/codex/blob/3e238776e857eccd3bde6bff3026e2e9798f6524/codex-rs/tui/src/app/thread_routing.rs#L475-L497)).
The rollout records both alike.

A copied fork has no boundary beyond the ancestor's `session_meta` and the
per-message `inherited_user_message` flag, so the other copied records stay
in the fork's file under the fork's session id.

## 14. Confidence

High: everything in [section 2](#2-per-user-storage) to [section
6](#6-where-the-project-path-is-recorded) cited to source, and the local listing matches. Medium:
desktop app sharing `~/.codex` (issue tracker and write-ups, not source). High (observed on Windows,
Codex Desktop 0.162.0-alpha.17.2): the desktop-only files and tables in [Codex Desktop inside the
ChatGPT app](#codex-desktop-inside-the-chatgpt-app) and the credentials they add. High (observed on
Ubuntu 26.04.1, Codex CLI 0.162.1): [Standalone CLI on Linux](#standalone-cli-on-linux). High
(observed on macOS 26.6.2, Codex Desktop and Codex CLI 0.162.1): [macOS
differences](#macos-differences). High (observed, Codex CLI 0.162.1 standalone on Windows): the
layout in [Standalone CLI on Windows](#standalone-cli-on-windows). High (observed on macOS 26.6.2,
Codex Desktop 0.163.0-alpha.10.2 inside ChatGPT 26.1013.40934, one step per listing): [macOS,
ChatGPT 26.1013.40934](#macos-chatgpt-26101340934) and the shell snapshot contents. Medium:
`cap_sid` holding capability SIDs (inferred from key names and value lengths). Not determined: what
`tui-thread-reference-capabilities/<thread uuid>` records beyond its 0-byte name; whether
`.sandbox*` dirs exist on non-Windows hosts; where remote control's server token is kept; the
purpose of `.codex-provisioning-*.guard` beyond its name.
